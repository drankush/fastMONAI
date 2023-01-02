# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/09_external_data.ipynb.

# %% auto 0
__all__ = ['MURLs', 'download_ixi_data', 'download_spine_test_data', 'download_example_spine_data']

# %% ../nbs/09_external_data.ipynb 2
from pathlib import Path
from glob import glob
import pandas as pd
from monai.apps import download_url, download_and_extract

# %% ../nbs/09_external_data.ipynb 4
class MURLs():
    '''A class with external medical dataset URLs.'''

    IXI_DATA = 'http://biomedic.doc.ic.ac.uk/brain-development/downloads/IXI/IXI-T1.tar'
    IXI_DEMOGRAPHIC_INFORMATION = 'http://biomedic.doc.ic.ac.uk/brain-development/downloads/IXI/IXI.xls'
    CHENGWEN_CHU_SPINE_DATA = 'https://drive.google.com/uc?id=1rbm9-KKAexpNm2mC9FsSbfnS8VJaF3Kn&confirm=t'
    EXAMPLE_SPINE_DATA = 'https://drive.google.com/uc?id=1Ms3Q6MYQrQUA_PKZbJ2t2NeYFQ5jloMh'

# %% ../nbs/09_external_data.ipynb 5
def _process_ixi_xls(xls_path:(str, Path), img_path: Path):
    '''Private method to process the demographic information for the IXI dataset.

    Args:
        xls_path: File path to the xls file with the demographic information.
        img_path: Folder path to the images

    Returns:
        DataFrame: A processed dataframe with image path and demographic information.
    '''

    print('Preprocessing ' + str(xls_path))

    df = pd.read_excel(xls_path)

    duplicate_subject_ids = df[df.duplicated(['IXI_ID'], keep=False)].IXI_ID.unique()

    for subject_id in duplicate_subject_ids:
        age = df.loc[df.IXI_ID == subject_id].AGE.nunique()
        if age != 1: df = df.loc[df.IXI_ID != subject_id] #Remove duplicates with two different age values

    df = df.drop_duplicates(subset='IXI_ID', keep='first').reset_index(drop=True)

    df['subject_id'] = ['IXI' + str(subject_id).zfill(3) for subject_id in df.IXI_ID.values]
    df = df.rename(columns={'SEX_ID (1=m, 2=f)': 'gender'})
    df['age_at_scan'] = df.AGE.round(2)
    df = df.replace({'gender': {1:'M', 2:'F'}})

    img_list = list(img_path.glob('*.nii.gz'))
    for path in img_list:
        subject_id = path.parts[-1].split('-')[0]
        df.loc[df.subject_id == subject_id, 't1_path'] = path

    df = df.dropna()
    df = df[['t1_path', 'subject_id', 'gender', 'age_at_scan']]
    return df

# %% ../nbs/09_external_data.ipynb 6
def download_ixi_data(path:(str, Path)='../data' # Path to the directory where the data will be stored
                     ):
    '''Download T1 scans and demographic information from the IXI dataset, then process the demographic 
        information for each subject and save the information as a CSV file.
    Returns path to the stored CSV file.
    '''
    path = Path(path)/'IXI'
    img_path = path/'T1_images' 

    # Check whether image data already present in img_path:
    is_extracted=False
    try:
        if len(list(img_path.iterdir())) >= 581: # 581 imgs in the IXI dataset
            is_extracted=True
            print(f"Images already downloaded and extracted to {img_path}")
    except:
        is_extracted=False

    # Download and extract images
    if not is_extracted: 
        download_and_extract(url=MURLs.IXI_DATA, filepath=path/'IXI-T1.tar', output_dir=img_path)
        (path/'IXI-T1.tar').unlink()


    # Download demographic info
    download_url(url=MURLs.IXI_DEMOGRAPHIC_INFORMATION, filepath=path/'IXI.xls')

    processed_df = _process_ixi_xls(xls_path=path/'IXI.xls', img_path=img_path)
    processed_df.to_csv(path/'dataset.csv',index=False)

    return path

# %% ../nbs/09_external_data.ipynb 7
def _create_spine_df(test_dir:Path):
    # Get a list of the image files in the 'img' directory
    img_list = glob(str(test_dir/'img/*.nii.gz'))

    # Create a list of the corresponding mask files in the 'seg' directory
    mask_list = [str(fn).replace('img', 'seg') for fn in img_list]

    # Create a list of the subject IDs for each image file
    subject_id_list = [fn.split('_')[-1].split('.')[0] for fn in mask_list]
    
    # Create a dictionary containing the test data
    test_data = {'t2_img_path':img_list, 't2_mask_path':mask_list, 'subject_id':subject_id_list, 'is_test':True}

    # Create a DataFrame from the example data dictionary
    return pd.DataFrame(test_data)

# %% ../nbs/09_external_data.ipynb 8
def download_spine_test_data(path:(str, Path)='../data'):
    
    ''' Download T2w scans from 'Fully Automatic Localization and Segmentation of 3D Vertebral Bodies from CT/MR Images via a Learning-Based Method' study by Chu et. al. 
    Returns a processed dataframe with image path, label path and subject IDs. 
    '''
    study = 'chengwen_chu_2015'
    
    download_and_extract(url=MURLs.CHENGWEN_CHU_SPINE_DATA, filepath=f'{study}.zip', output_dir=path)
    Path(f'{study}.zip').unlink()
    
    return _create_spine_df(Path(path)/study)

# %% ../nbs/09_external_data.ipynb 9
def download_example_spine_data(path:(str, Path)='../data'): 
    
    '''Download example T2w scan and predicted mask.'''
    study = 'example_data'
    
    download_and_extract(url=MURLs.EXAMPLE_SPINE_DATA, filepath='example_data.zip', output_dir=path);
    Path('example_data.zip').unlink()
    
    return Path(path/study)
