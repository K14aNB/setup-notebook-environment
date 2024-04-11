from setuptools import setup,find_packages

setup(
    name='env_setup',
    version='0.1.0',
    author='K14aNB',
    author_email='kirnid4@gmail.com',
    description='Python script to perform Google Colab/Jupyter Notebook environment setup tasks',
    packages=find_packages(),
    install_requires=['git+https://github.com/K14aNB/download-kaggle-dataset.git@main']
    )