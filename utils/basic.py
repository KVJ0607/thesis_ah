import itertools
from datetime import datetime
def create_nd_list(dimensions, value=[]):
    """Creating an n-dimensional list variable dimensions 

    Args:
        dimensions (_type_): [d1, d2, ..., dn]
        value (int, optional): element value. Defaults to 0.

    Returns:
        _type_: an n-dimensional list with dimensional d1,d2,...,dn 
    E.g.:
        dims = [2, 3, 4]  # Replace with your dimensions [d1, d2, ..., dn]
        nd_list = create_nd_list(dims)
        print(nd_list)
        > [[[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]]
    """
    if not dimensions:
        return value
    return [create_nd_list(dimensions[1:], value) for _ in range(dimensions[0])]

def flatten_list_element(unevent_list:list|tuple,base_type)->list: 
    flatten_list_=[]
    for ele in unevent_list:
        if type(ele)==base_type:
            flatten_list_.append(ele)
        else:
            flatten_list_=flatten_list_+flatten_list_element(ele,base_type)
    return flatten_list_    

def iterate_indexes(list_of_dimension_size:list[int])->list: 
    """ return get all the indexes cross product
    e.g. index_list=iterate_indexes([2,2,2])
         index_list 
         >>>[(0,0,0),(0,0,1),(0,1,0),(0,1,1),(1,0,0),(1,0,1),(1,1,0),(1,1,1)]

    Args:
        list_of_dimension_size (list[int]): its element corrsponding the size of a dimension

    Returns:
        list: an iterable list like object
    """
    if len(list_of_dimension_size)<2: 
        result=[]
        for i in range(list_of_dimension_size[0]): 
            new_ele=list()
            new_ele.append(i)
            result.append(tuple(new_ele))
        return result
        
    result=itertools.product(range(list_of_dimension_size[0]),range(list_of_dimension_size[1]))
    for dim_size in list_of_dimension_size[2:]: 
        new_d=range(dim_size)
        result=itertools.product(result,new_d)
    return result

def get_element_from_list_with_indexes(nd_list, index_list):
    """retrieve an element from an n-dimensional list (or nested lists) given a list of indexes
    """
    element = nd_list
    for idx in index_list:
        element = element[idx]
    return element

def set_element_of_list_with_indexes(nd_list, index_list, value)->None:
    """set one value into one element in a list 

    Args:
        nd_list (_type_): the list to be altered
        index_list (_type_): list of indexes point to the element to be altered. e.g. index_list=[2,3,1] is nd_list[2][3][1]
        value (_type_): the value to be input to the list 
    """
    def _supports_item_assignment(obj):
        return hasattr(obj, '__setitem__')
    

    # Get to the element one level above the target
    element = nd_list
    for idx in index_list[:-1]:  # Go up to the second-to-last index
        element = element[idx]
    
    # Set the value at the final index
    final_index = index_list[-1]  # Get the last index
    element[final_index] = value
    
def convert_to_iso_hkexnews(datetime_str):
    
    # Define the input format and the format for ISO 8601
    input_format = '%d/%m/%Y %H:%M'
    iso_format = '%Y-%m-%dT%H:%M:%S'
    
    # Parse the input string into a datetime object
    datetime_obj = datetime.strptime(datetime_str, input_format)
    
    # Convert the datetime object to a string in ISO 8601 format
    iso_datetime_str = datetime_obj.strftime(iso_format)
    
    return iso_datetime_str

