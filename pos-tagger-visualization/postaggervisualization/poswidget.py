import Orange.data
from orangewidget.widget import OWBaseWidget, Input, Output
from orangewidget.utils.widgetpreview import WidgetPreview
from Orange.widgets.utils.concurrent import ConcurrentWidgetMixin, TaskState
from orangecontrib.text.widgets.utils import asynchronous
from orangewidget import gui, settings
from AnyQt.QtWidgets import QTableWidget, QTableView, QPlainTextEdit
from AnyQt.QtCore import QAbstractTableModel, Qt, QModelIndex
from AnyQt.QtGui import QColor
from PyQt5.QtCore import pyqtSignal, QThread, QObject, QRunnable, Qt, QThreadPool
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice, QBarSeries, QBarCategoryAxis,QValueAxis, QBarSet
from Orange.data import StringVariable
from orangecontrib.text import Corpus, preprocess
from orangecontrib.text.preprocess import PreprocessorList
from nltk.tokenize import word_tokenize
from polyglot.detect import Detector
from polyglot.text import Text
import pandas as pd 
import numpy as np  

class POStaggerVisualization(OWBaseWidget):

    name = "POS tagger visualization"
    description = "Implementing part-of-speech tagging."
    icon = ""
    priority = 510

    
    class Inputs:
        input_data = Input("Corpus", Corpus)


    #da li zelimo da imamo i desni deo, tj glavni prikaz osim kontrolnog
    want_main_area = True
    #za izbor tipa grafikona
    method_idx=settings.Setting(1)
    #resizing_enabled= False
    
    def __init__(self):
        super().__init__()
        self.corpus= None
        self.pp_corpus = None
        self.chartMain = QChartView()

        # GUI
        self.mainArea.layout().addWidget(self.chartMain)
        self.boxInfo = gui.widgetBox(self.controlArea, "Info")
        self.infoTextLoaded = gui.widgetLabel(self.boxInfo, 'No data on input yet, waiting to get data.')
        self.infoNumberOfDocsLoaded = gui.widgetLabel(self.boxInfo, '')
        self.infoLanguageDetected = gui.widgetLabel(self.boxInfo, '')

        self.boxDfView = gui.widgetBox(self.controlArea, "Part of speech table view")
        self.infoDf = gui.widgetLabel(self.boxDfView, '')

        self.boxOptions = box = gui.radioButtonsInBox(self.controlArea,self,"method_idx", box="Graph type selection")
        self.pie_chart_radio_button = gui.appendRadioButton(box,"Pie chart", addToLayout=True)
        self.bar_chart_radio_button = gui.appendRadioButton(box,"Bar chart", addToLayout=True)

        self.infoc = gui.widgetLabel(self.boxInfo, '')
        self.longRunningBtn = gui.button(self.controlArea, self, "Commit", callback=self.graph_choice, focusPolicy=Qt.NoFocus)
        self.longRunningBtn.setDisabled(True)

    

    @Inputs.input_data
    def set_data(self, data=None):
        self.corpus = data
        self.pp_corpus = None
        if self.corpus is not None:
            self.infoTextLoaded.setText('Text succesfully loaded.\n')
            self.longRunningBtn.setDisabled(False)
            #obrada se razlikuje u zavisnosti da li je tekst prethodno procesiran ili ne
            if  self.corpus.has_tokens():
                text = ' '
                for i in range(len(self.corpus.documents)): 
                    text+=' '
                    text+= ' '.join(self.corpus.tokens[i])
                self.pp_corpus = text
            else:
                self.pp_corpus = ' '.join(self.corpus.documents)

            self.infoNumberOfDocsLoaded.setText('Number of documents loaded: ' + str(len(self.corpus.documents)))
            self.language_detection()
            self.pos_tag_visualization()
            self.update_widget()
           
        else: 
            self.infoTextLoaded.setText('No data on input yet, waiting to get something.')
    
    
    def graph_choice(self):
        self.update_widget()
        

    def update_widget(self):   
        widget= self.mainArea.layout().itemAt(0).widget()
        if widget:
            self.mainArea.layout().removeWidget(widget)
        if self.method_idx == 0 :
            self.pos_tag_pie_chart()
        else: 
            self.pos_tag_bar_chart()
    

    def language_detection(self):
        text = self.pp_corpus
        detector = Detector(text)
        textPreprocessed = str(detector.language)
        lang= (Text(textPreprocessed).words)[2] 
        confidence = (Text(textPreprocessed).words)[8]
        textToShow = lang + ' was detected with confidence percentage of : ' + confidence 
        self.infoLanguageDetected.setText(textToShow)

    def pos_tag_visualization(self):
        word_types=[]
        word_text=[]
        text = Text(self.pp_corpus)
        length= len(text.pos_tags)
        for i in range(length):
            word_types.append(text.pos_tags[i][1])
            word_text.append(text.pos_tags[i][0])
        df = pd.DataFrame(list(zip(word_types,word_text)), columns=['Word type', 'value'])
        self.infoDf.setText(str(df))

    
    def pos_tag_bar_chart(self):
        labels = ['ADJ','ADP', 'ADV','AUX','CONJ','DET','INTJ','NOUN','NUM','PART','PRON','PROPN','PUNCT','SCONJ','SYM','VERB','X']
        text = Text(self.pp_corpus)
        length= len(text.pos_tags)
        pos_list = [0] * len(labels) #inicijalizacija na 0 za sve elemente liste
        pos_list_perc= [0] * len(labels)
        #kategorije u koje se mogu svrstati reci
        for i in range(length):
            if(text.pos_tags[i][1]=='ADJ'):
                pos_list[0]+=1
            elif (text.pos_tags[i][1]=='ADP'):
                pos_list[1]+=1
            elif(text.pos_tags[i][1] == 'ADV'):
                pos_list[2]+=1
            elif(text.pos_tags[i][1] == 'AUX'):
                pos_list[3]+=1
            elif(text.pos_tags[i][1] == 'CONJ'):
                pos_list[4]+=1
            elif(text.pos_tags[i][1] == 'DET'):
                pos_list[5]+=1
            elif(text.pos_tags[i][1] == 'INTJ'):
                pos_list[6]+=1
            elif(text.pos_tags[i][1] == 'NOUN'):
                pos_list[7]+=1
            elif(text.pos_tags[i][1] == 'NUM'):
                pos_list[8]+=1
            elif(text.pos_tags[i][1] == 'PART'):
                pos_list[9]+=1
            elif(text.pos_tags[i][1] == 'PRON'):
                pos_list[10]+=1
            elif(text.pos_tags[i][1] == 'PROPN'):
                pos_list[11]+=1
            elif(text.pos_tags[i][1] == 'PUNCT'):
                pos_list[12]+=1
            elif(text.pos_tags[i][1] == 'SCONJ'):
                pos_list[13]+=1
            elif(text.pos_tags[i][1] == 'SYM'):
                pos_list[14]+=1
            elif(text.pos_tags[i][1] == 'VERB'):
                pos_list[15]+=1
            else:
                pos_list[16]+=1
        chart = QChart()

        series = QBarSeries()
        set = QBarSet(" ")
        set.append(pos_list)
        series.append(set)
        series.setLabelsVisible(True)
        chart.addSeries(series)
        
        chart.setTitle("Part of speech tagging bar chart")
        axisX = QBarCategoryAxis()
        axisX.append(labels)
        chart.addAxis(axisX,Qt.AlignBottom)
        series.attachAxis(axisX)
        axisY = QValueAxis()
        axisY.setRange(0, max(pos_list))
        chart.addAxis(axisY,Qt.AlignLeft)
        series.attachAxis(axisY)

        self.chartMain = QChartView(chart)
        self.mainArea.layout().addWidget(self.chartMain)
        
    
    def pos_tag_pie_chart(self):
        labels = ['ADJ','ADP', 'ADV','AUX','CONJ','DET','INTJ','NOUN','NUM','PART','PRON','PROPN','PUNCT','SCONJ','SYM','VERB','X']
        text = Text(self.pp_corpus)
        length= len(text.pos_tags)
        pos_list = [0] * len(labels) #inicijalizacija na 0 za sve elemente liste
        pos_list_perc= [0] * len(labels)
        #kategorije u koje se mogu svrstati reci
        for i in range(length):
            if(text.pos_tags[i][1]=='ADJ'):
                pos_list[0]+=1
            elif (text.pos_tags[i][1]=='ADP'):
                pos_list[1]+=1
            elif(text.pos_tags[i][1] == 'ADV'):
                pos_list[2]+=1
            elif(text.pos_tags[i][1] == 'AUX'):
                pos_list[3]+=1
            elif(text.pos_tags[i][1] == 'CONJ'):
                pos_list[4]+=1
            elif(text.pos_tags[i][1] == 'DET'):
                pos_list[5]+=1
            elif(text.pos_tags[i][1] == 'INTJ'):
                pos_list[6]+=1
            elif(text.pos_tags[i][1] == 'NOUN'):
                pos_list[7]+=1
            elif(text.pos_tags[i][1] == 'NUM'):
                pos_list[8]+=1
            elif(text.pos_tags[i][1] == 'PART'):
                pos_list[9]+=1
            elif(text.pos_tags[i][1] == 'PRON'):
                pos_list[10]+=1
            elif(text.pos_tags[i][1] == 'PROPN'):
                pos_list[11]+=1
            elif(text.pos_tags[i][1] == 'PUNCT'):
                pos_list[12]+=1
            elif(text.pos_tags[i][1] == 'SCONJ'):
                pos_list[13]+=1
            elif(text.pos_tags[i][1] == 'SYM'):
                pos_list[14]+=1
            elif(text.pos_tags[i][1] == 'VERB'):
                pos_list[15]+=1
            else:
                pos_list[16]+=1
        #kod za pie chart u qt-u
        series = QPieSeries()
        for i in range(len(labels)):
            pos_list_perc[i]= (pos_list[i]/len(text.pos_tags)*100)
            series.append(labels[i], int(pos_list_perc[i]))
            slice = series.slices()[i]
            label = str(round(pos_list_perc[i],2))
            slice.setLabel(label)
            #slice.setColor(QColor(colors[i]))
            if(pos_list_perc[i] > 0.1):
                slice.setLabelVisible()
    
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle('Part of speech tagging pie chart')
        
        for i in range(len(labels)):
            chart.legend().markers(series)[i].setLabel(labels[i])
        
        self.chartMain = QChartView(chart)

        self.mainArea.layout().addWidget(self.chartMain)

        
    if __name__ == "__main__":
        from Orange.widgets.utils.widgetpreview import WidgetPreview  # since Orange 3.20.0
        WidgetPreview(MyWidget).run()    






