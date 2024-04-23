import os
import platform
from subprocess import run,CalledProcessError
import yaml
from urllib3 import PoolManager
from download_kaggle_dataset import download
from zipfile import ZipFile

def setup(repo_name:str,nb_name:str):
    '''
    Python script to perform Google Colab/Jupyter Notebook environment setup tasks
    like downloading of datasets from source specified in config, 
    handling output formats (html, py:percent).
    
    Arguments:
    repo_name:str : Local git repository name
    nb_name:str : Currently active Colab/Jupyter Notebook
    
    Returns:str : result_path is the directory where data is downloaded
    '''
    # Check if OS is 'Linux', 'Windows' or 'OSX'
    if platform.system()=='Linux':
        pltfrm='linux'
    elif platform.system()=='Windows':
        pltfrm='windows'
    elif platform.system()=='Darwin':
        pltfrm='osx'
       

    # Detect currently active runtime
    try:
        if get_ipython().__class__.__module__=='google.colab._shell':
            runtime='colab'
        elif get_ipython().__class__.__module__=='ipykernel.zmqshell':
            runtime='jupyter'
    except NameError as ne:
        print('Running as .py Script and not as .ipynb Notebook')
        runtime='python-script'


    # Get parent path
    parent_path=''
    if runtime in ['google_colab','jupyter']:
        parent_path=os.getcwd()
    elif runtime=='python-script' and pltfrm=='linux':
        if os.path.exists(os.path.join('/mnt','chromeos','GoogleDrive','MyDrive')):
            parent_path=os.path.join('/mnt','chromeos','GoogleDrive','MyDrive')
        

    
    # Get repo_path from repo_name
    repo_path=''
    try:
        find_cmd_results=run(['find',parent_path,'-maxdepth','5','-name',repo_name,'-type','d'],capture_output=True,check=True)
        repo_path=find_cmd_results.stdout.decode('utf-8').replace('\n','',1)
    except CalledProcessError as e1:
        print(f'{e1.cmd} failed')
    except IndexError as e2:
        print('Repo not found')

    
    # Read the config.yaml
    try:
        with open(os.path.join(repo_path,'configs','config.yaml')) as f:
            try:
                config_details = yaml.safe_load(f)
            except yaml.YAMLError as ex:
                print(ex)
    except FileNotFoundError as fnf:
        print(fnf)
        print('config.yaml not found in repo')
                    
    # Data
    notebooks=config_details['notebooks']
    data=notebooks[nb_name].get('data')
    data_src_type=data[0].get('source')
    data_src_path=data[1].get('data-src-path')

    # Outputs
    outputs=notebooks[nb_name].get('outputs')
    nb_html_preview=outputs[0].get('nb-html-preview')
    py_percent_script=outputs[1].get('py-percent-script')
    output_path=outputs[2].get('output-path')

    # Set up Data
    result_path=''
    if data_src_type=='kaggle-datasets':
        if runtime=='colab':
            if os.path.isdir('/content/data') is True and len(os.listdir(os.path.join('/content','data')))>0:
                result_path='/content/data'
            else:
                result_path=download(data_src_path=data_src_path,colab=True)
        elif runtime in ['jupyter','python-script']:
            if os.path.isdir(os.path.join(repo_path,'data',nb_name)) is True and len(os.listdir(os.path.join(repo_path,'data',nb_name)))>0:
                result_path=os.path.join(repo_path,'data',nb_name)
            else:
                result_path=download(data_src_path=data_src_path,colab=False,repo_path=repo_path,nb_name=nb_name)
    elif data_src_type=='direct-download':
        if runtime=='colab' and os.path.isfile(os.path.join('/content','data',data_src_path.split('/')[-1])) is True:
            result_path='/content/data'
        elif runtime in ['jupyter','python-script'] and os.path.isfile(os.path.join(repo_path,'data',nb_name,data_src_path.split('/')[-1])) is True:
            result_path=os.path.join(repo_path,'data',nb_name)
        else:
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
                result_path=os.path.join(repo_path,'data',nb_name)
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
        if nb_html_preview == 'true':
            # Converting the notebook to HTML output format for preview in GitHub
            try:
                run(['jupyter','nbconvert','--to','html',os.path.join(repo_path,output_path,nb_name+'.ipynb')],check=True)
            except CalledProcessError as e3:
                print(f'{e3.cmd} failed')
                
        if py_percent_script == 'true':
            # Try importing jupytext. If not installed in colab VM, install the module.
            try:
                __import__('jupytext')
            except ImportError:
                try:
                    run(['python','-m','pip','install','jupytext','-q'],check=True)
                except CalledProcessError as e4:
                    print(f'{e4.cmd} failed')
            
            # Converting the notebook to py:percent script format
            try:
                run(['jupytext','--to','py:percent',os.path.join(repo_path,output_path,nb_name+'.ipynb')],check=True)
            except CalledProcessError as e5:
                print(f'{e5.cmd} failed')

            py_filename = os.path.join(repo_path,output_path,nb_name+'.py')
            # Check if jupytext config file does not exist in colab VM, create it.
            # This jupytext config file is essential for clearing cell metadata added by colab
            try:
                run(['jupytext','--opt', 'cell_metadata_filter=-all',py_filename],check=True)
            except CalledProcessError as e6:
                print(f'{e6.cmd} failed')
    return result_path
    