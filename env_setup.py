import os
import platform
from subprocess import run,CalledProcessError
import yaml
from urllib3 import PoolManager
from download_kaggle_dataset import download
from zipfile import ZipFile

def setup(repo_path:str,nb_name:str):
    '''
    Python script to perform Google Colab/Jupyter Notebook environment setup tasks
    like downloading of datasets from source specified in config, 
    handling output formats (html, py:percent).
    
    Arguments:
    repo_path:str : Relative path of the local git repository name which will be joined with its parent_path,
    nb_name:str : Currently active Colab/Jupyter Notebook
    
    Returns:str : result_path is the directory where data is downloaded
    '''
    # Check if OS is 'Linux', 'Windows' or 'OSX'
    # if platform.system()=='Linux':
    #     pltfrm='linux'
    # elif platform.system()=='Windows':
    #     pltfrm='windows'
    # elif platform.system()=='Darwin':
    #     pltfrm='osx'
       

    # Detect currently active runtime
    try:
        if get_ipython().__class__.__module__=='google.colab._shell':
            runtime='colab'
        elif get_ipython().__class__.__module__=='ipykernel.zmqshell':
            runtime='jupyter'
    except NameError as ne:
        print('Running as .py Script and not as .ipynb Notebook')
        runtime='python-script'

    if repo_path.startswith('.'):
        repo_path=repo_path.replace('./','',1)
    
    repo_abs_path=os.path.join(os.getcwd(),repo_path)


    
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
    result_path=''
    if data_src_type=='kaggle-datasets':
        if runtime=='colab':
            if os.path.isdir('/content/data') is False or os.listdir(os.path.join('/content,data'))==[]:
                result_path=download(data_src_path=data_src_path,colab=True)               
        elif runtime in ['jupyter','python-script']:
            if os.path.isdir(os.path.join(repo_abs_path,'data',nb_name)) is False or os.listdir(os.path.join(repo_abs_path,'data',nb_name))==[]:
                result_path=download(data_src_path=data_src_path,colab=False,repo_path=repo_abs_path,nb_name=nb_name)
    elif data_src_type=='direct-download':
        if os.path.isfile(os.path.join('/content','data',data_src_path.split('/')[-1])) is False or \
        os.path.isfile(os.path.join(repo_abs_path,'data',nb_name,data_src_path.split('/')[-1])) is False:
            http = PoolManager()
            download_response=http.request('GET',data_src_path)
        if runtime=='colab':
            result_path='/content/data'
            if os.path.isdir(result_path) is False:
                os.mkdir(result_path)
                if download_response.status==200:
                    with open(os.path.join(result_path,data_src_path.split('/')[-1]),'w') as d:
                        d.write(download_response.data.decode('utf-8'))
                    if os.listdir(result_path)[0].endswith('.zip') is True:
                        with ZipFile(os.path.join(result_path,os.listdir(result_path)[0]),'r') as zip:
                            zip.extractall(path=result_path)
            
        elif runtime in ['jupyter','python-script']:
            result_path=os.path.join(repo_abs_path,'data',nb_name)
            if os.path.isdir(result_path) is False:
                os.makedirs(result_path)
            if download_response.status==200:
                with open(os.path.join(result_path,data_src_path.split('/')[-1]),'w') as dl:
                    dl.write(download_response.data.decode('utf-8'))
                if os.listdir(result_path)[0].endswith('.zip') is True:
                    with ZipFile(os.path.join(result_path,os.listdir(result_path)[0]),'r') as zip:
                        zip.extractall(path=result_path)


   # Handling Outputs

    if runtime in ['colab','jupyter']:
        if nb_outputs.get('nb-html-preview') == 'true':
            # Converting the notebook to HTML output format for preview in GitHub
            try:
                run(['jupyter','nbconvert','--to','html',os.path.join(repo_abs_path,nb_outputs.get('output-path'),nb_name+'.ipynb')],check=True)
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
                run(['jupytext','--to','py:percent',os.path.join(repo_abs_path,nb_outputs.get('output-path'),nb_name+'.ipynb')],check=True)
            except CalledProcessError as e3:
                print(f'{e3.cmd} failed')

            py_filename = os.path.join(repo_abs_path,nb_outputs.get('output-path'),nb_name+'.py')
            # Check if jupytext config file does not exist in colab VM, create it.
            # This jupytext config file is essential for clearing cell metadata added by colab
            try:
                run(['jupytext','--opt', 'cell_metadata_filter=-all',py_filename],check=True)
            except CalledProcessError as e4:
                print(f'{e4.cmd} failed')
    return result_path
    