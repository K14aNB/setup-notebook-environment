import os
import platform
import sys
from subprocess import run,CalledProcessError
import yaml
from urllib3 import request,PoolManager
from zipfile import ZipFile

def setup(repo_path:str,nb_name:str):
    '''
    Python script to perform Google Colab/Jupyter Notebook environment setup tasks
    like downloading of datasets from source specified in config, 
    handling output formats (html, py:percent).
    
    Arguments:
    repo_path:str : Local git repository name which will be joined with its absolute path 
                    depending on the environment type.
    nb_name:str : Currently active Colab/Jupyter Notebook 
    Returns: None
    '''
    # Check if OS is 'Linux', 'Windows' or 'OSX'
    if platform.system()=='Linux':
        pltfrm='linux'
    elif platform.system()=='Windows':
        pltfrm='windows'
    elif platform.system()=='Darwin':
        pltfrm='osx'
       
    
    # Check if Google Colab runtime or Local Runtime is currently active
    if 'google.colab' in sys.modules:
        runtime='colab'
    else:
        runtime='local'
    
    parent_path=''

    # Set parent path
    # if connected to colab runtime, parent path = '/content/drive'
    # if connected to local jupyter runtime, parent path = '/mnt..'
    # or specific drive letter
    if runtime=='colab':
        parent_path = '/content/drive/MyDrive'        
    elif runtime=='local' and pltfrm in ['linux','windows']:
        parent_path = os.getcwd()
    
    repo_abs_path = os.path.join(parent_path,'Data Science','Git Repos',repo_path)

    
    # Read the config.yaml
    with open(os.path.join(repo_abs_path,'configs','config.yaml')) as f:
            try:
                config_details = yaml.safe_load(f)
            except yaml.YAMLError as ex:
                print(ex)
                    
    # Data
    data=config_details['data']
    data_src=data.get(nb_name)
    data_src_type=data_src.get('source')
    data_src_path=data_src.get('data-src-path')

    # Outputs
    outputs=config_details['outputs']
    nb_outputs=outputs.get(nb_name)

    # Set up Data
    if data_src_type=='kaggle-datasets':
        http = PoolManager()
        kaggle_response = http.request('GET','https://gist.githubusercontent.com/K14aNB/c2e72aa3d250e421f89fdf232913d4ff/raw/')
        namespace={}
        if runtime=='colab':
            if os.path.isdir('/content/data') is False:
                if kaggle_response.status==200:
                    exec(kaggle_response.data.decode('utf-8'),namespace)
                    namespace['download'](data_src_path=data_src_path,colab=True)               
        elif runtime=='local':
            if os.path.isdir(os.path.join(repo_abs_path,'data')) is False:
                if kaggle_response.status==200:
                    exec(kaggle_response.data.decode('utf-8'),namespace)
                    namespace['download'](data_src_path=data_src_path,colab=False,repo_path=repo_abs_path)
    elif data_src_type=='direct-download':
        http = PoolManager()
        download_response = http.request('GET',data_src_path)
        if runtime=='colab':
            if os.path.isdir('/content/data') is False:
                os.mkdir('/content/data')
                if download_response.status==200:
                    with open('/content/data/'+data_src_path.split('/')[-1],'w') as d:
                        d.write(download_response.data.decode('utf-8'))
                if os.listdir('/content/data')[0].endswith('.zip') is True:
                    with ZipFile(os.path.join('/content','data',os.listdir('/content/data')[0]),'r') as zip:
                        zip.extractall(path=os.path.join('/content','data'))
        else:
            if os.path.isdir(os.path.join(repo_abs_path,'data')) is False:
                os.mkdir(os.path.join(repo_abs_path,'data'))
                if download_response.status==200:
                    with open(os.path.join(repo_abs_path,'data',data_src.split('/')[-1]),'w') as dl:
                        dl.write(download_response.data.decode('utf-8'))
                if os.listdir(os.path.join(repo_abs_path,'data'))[0].endswith('.zip') is True:
                    with ZipFile(os.path.join(repo_abs_path,'data',os.listdir(os.path.join(repo_abs_path,'data')[0])),'r') as zip:
                        zip.extractall(path=os.path.join(repo_abs_path,'data'))

   # Handling Outputs

    if nb_outputs.get('nb-html-preview') == 'true':
        # Converting the notebook to HTML output format for preview in GitHub
        try:
            run(['jupyter','nbconvert','--to','html',os.path.join(parent_path,'Data Science','Git Repos',nb_outputs.get('output-path'),nb_name+'.ipynb')],check=True)
        except CalledProcessError as e1:
            print(f'{e1.cmd} failed')
             
    if nb_outputs.get('py-percent-script') == 'true':
        # Try importing jupytext. If not installed in colab VM, install the module.
        try:
            __import__('jupytext')
        except ImportError:
            try:
                run(['python','-m','pip','install','jupytext','-q'],check=True)
            except CalledProcessError as e2:
                print(f'{e2.cmd} failed')
        
        # Converting the notebook to py:percent script format
        try:
            run(['jupytext','--to','py:percent',os.path.join(parent_path,'Data Science','Git Repos',nb_outputs.get('output-path'),nb_name+'.ipynb')],check=True)
        except CalledProcessError as e3:
            print(f'{e3.cmd} failed')

#         if runtime=='colab':
        py_filename = os.path.join(parent_path,'Data Science','Git Repos',nb_outputs.get('output-path'),nb_name+'.py')
        # Check if jupytext config file does not exist in colab VM, create it.
        # This jupytext config file is essential for clearing cell metadata added by colab
        try:
            run(['jupytext','--opt', 'cell_metadata_filter=-all',py_filename],check=True)
        except:
            print(f'{e2.cmd} failed')