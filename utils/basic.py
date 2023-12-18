import itertools

def create_nd_list(dimensions, value=0):
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


def flatten_list(ele:tuple,base_type)->list: 
    new_ele=list(ele)
    result=[]
    if type(new_ele) == base_type: 
        return new_ele 
    else: 
        for ele in new_ele: 
            result=result+flatten_list(ele,base_type)
    return result
    
    
def flatten_list_element(unevent_list:list|tuple,base_type)->list: 
    flatten_list=[]
    for ele in unevent_list: 
        flatten_list.append(flatten_list(ele,base_type))
    return flatten_list    

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
        return list_of_dimension_size
    result=itertools.product(range(list_of_dimension_size[0]),range(list_of_dimension_size[1]))
    for dim_size in list_of_dimension_size[2:]: 
        new_d=range(dim_size)
        result=itertools.product(result,new_d)
    result=flatten_list_element(list(result),int)
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
    # Get to the element one level above the target
    element = nd_list
    for idx in index_list[:-1]:  # Go up to the second-to-last index
        element = element[idx]
    
    # Set the value at the final index
    final_index = index_list[-1]  # Get the last index
    element[final_index] = value
    