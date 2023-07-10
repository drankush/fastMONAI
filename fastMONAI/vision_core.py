# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_vision_core.ipynb.

# %% auto 0
__all__ = ['med_img_reader', 'MetaResolver', 'MedBase', 'MedImage', 'MedMask']

# %% ../nbs/01_vision_core.ipynb 2
from .vision_plot import *
from fastai.data.all import *
from torchio import ScalarImage, LabelMap, ToCanonical, Resample

# %% ../nbs/01_vision_core.ipynb 5
def _preprocess(obj, reorder, resample):
    """Preprocesses the given object.

    Args:
        obj: The object to preprocess.
        reorder: Whether to reorder the object.
        resample: Whether to resample the object.

    Returns:
        The preprocessed object and its original size.
    """
    if reorder:
        transform = ToCanonical()
        obj = transform(obj)

    original_size = obj.shape[1:]

    if resample and not all(np.isclose(obj.spacing, resample)):
        transform = Resample(resample)
        obj = transform(obj)

    if MedBase.affine_matrix is None:
        MedBase.affine_matrix = obj.affine

    return obj, original_size

# %% ../nbs/01_vision_core.ipynb 6
def _load_and_preprocess(file_path, reorder, resample, dtype):
    """
    Helper function to load and preprocess an image.

    Args:
        file_path: Image file path.
        reorder: Whether to reorder data for canonical (RAS+) orientation.
        resample: Whether to resample image to different voxel sizes and dimensions.
        dtype: Desired datatype for output.

    Returns:
        tuple: Original image, preprocessed image, and its original size.
    """
    org_img = LabelMap(file_path) if dtype is MedMask else ScalarImage(file_path) #_load(file_path, dtype=dtype) 
    input_img, org_size = _preprocess(org_img, reorder, resample)
    
    return org_img, input_img, org_size

# %% ../nbs/01_vision_core.ipynb 7
def _multi_channel(image_paths: list, reorder: bool, resample: list, dtype, only_tensor: bool):
    """
    Load and preprocess multisequence data.

    Args:
        image_paths: List of image paths (e.g., T1, T2, T1CE, DWI).
        reorder: Whether to reorder data for canonical (RAS+) orientation.
        resample: Whether to resample image to different voxel sizes and dimensions.
        dtype: Desired datatype for output.
        only_tensor: Whether to return only image tensor.

    Returns:
        torch.Tensor: A stacked 4D tensor, if `only_tensor` is True.
        tuple: Original image, preprocessed image, original size, if `only_tensor` is False.
    """
    image_data = [_load_and_preprocess(image, reorder, resample, dtype) for image in image_paths]
    org_img, input_img, org_size = image_data[-1]

    tensor = torch.stack([img.data[0] for _, img, _ in image_data], dim=0)
    
    if only_tensor: 
        dtype(tensor) 

    input_img.set_data(tensor)
    return org_img, input_img, org_size


# %% ../nbs/01_vision_core.ipynb 8
def med_img_reader(file_path:(str, Path), # Image path
                   dtype=torch.Tensor, # Datatype (MedImage, MedMask, torch.Tensor)
                   reorder:bool=False, # Whether to reorder the data to be closest to canonical (RAS+) orientation.
                   resample:list=None, # Whether to resample image to different voxel sizes and image dimensions.
                   only_tensor:bool=True # Whether to return only image tensor
                  ):
    '''Load and preprocess medical image'''
        
    if isinstance(file_path, str) and ';' in file_path:
        return _multi_channel(file_path.split(';'), reorder, resample, dtype, only_tensor)

    org_img, input_img, org_size = _load_and_preprocess(file_path, reorder, resample, dtype)

    return dtype(input_img.data.type(torch.float)) if only_tensor else org_img, input_img, org_size

# %% ../nbs/01_vision_core.ipynb 10
class MetaResolver(type(torch.Tensor), metaclass=BypassNewMeta):
    '''A class to bypass metaclass conflict:
    https://pytorch-geometric.readthedocs.io/en/latest/_modules/torch_geometric/data/batch.html
    '''
    pass

# %% ../nbs/01_vision_core.ipynb 11
class MedBase(torch.Tensor, metaclass=MetaResolver):
    '''A class that represents an image object. Metaclass casts x to this class if it is of type cls._bypass_type.'''

    _bypass_type=torch.Tensor
    _show_args = {'cmap':'gray'}
    resample, reorder = None, False
    affine_matrix = None


    @classmethod
    def create(cls, fn: (Path, str, torch.Tensor), **kwargs):
        """
        Open a medical image and cast to MedBase object. If it is a torch.Tensor, cast to MedBase object.

        Args:
            fn: Image path or a 4D torch.Tensor.
            kwargs: Additional parameters.

        Returns:
            A 4D tensor as MedBase object.
        """
        if isinstance(fn, torch.Tensor):
            return cls(fn)

        return med_img_reader(fn, dtype=cls, resample=cls.resample, reorder=cls.reorder)

    @classmethod
    def item_preprocessing(cls, resample: (list, int, tuple), reorder: bool):
        """
        Change the values for the class variables `resample` and `reorder`.

        Args:
            resample: A list with voxel spacing.
            reorder: Whether to reorder the data to be closest to canonical (RAS+) orientation.
        """
        cls.resample = resample
        cls.reorder = reorder

    def show(self, ctx=None, channel=0, indices=None, anatomical_plane=0, **kwargs):
        """
        Show Medimage using `merge(self._show_args, kwargs)`.

        Returns:
            Shown image.
        """
        return show_med_img(
            self, ctx=ctx, channel=channel, indices=indices, 
            anatomical_plane=anatomical_plane, voxel_size=self.resample,  
            **merge(self._show_args, kwargs)
        )

    def __repr__(self):
        return f'{self.__class__.__name__} mode={self.mode} size={"x".join([str(d) for d in self.size])}'

# %% ../nbs/01_vision_core.ipynb 12
class MedImage(MedBase):
    '''Subclass of MedBase that represents an image object.'''
    pass

# %% ../nbs/01_vision_core.ipynb 13
class MedMask(MedBase):
    '''Subclass of MedBase that represents an mask object.'''
    _show_args = {'alpha':0.5, 'cmap':'tab20'}
