from setuptools import setup

setup(name="My component",
      packages=["postaggervisualization"],
      package_data={"postaggervisualization": ["icons/*.svg"]},
      classifiers=["Example :: Invalid"],
      # Declare postaggervisualization package to contain widgets for the "My component" category
      entry_points={"orange.widgets": "My component = postaggervisualization"},
      )