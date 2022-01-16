import copy
import os
import typing as _t
import waapi as _w
from . import constants as _c

# ------------------------------------------

_OnNameConflict3 = _t.Union[_t.Literal['rename'], _t.Literal['replace'], _t.Literal['fail']]
_OnNameConflict4 = _t.Union[_t.Literal['rename'], _t.Literal['replace'], _t.Literal['fail'], _t.Literal['merge']]
_InclusionOperation = _t.Union[_t.Literal['add'], _t.Literal['remove'], _t.Literal['replace']]
_ImportOperation = _t.Union[_t.Literal['createNew'], _t.Literal['useExisting'], _t.Literal['replaceExisting']]
_WaapiValue = _t.Union[float, str, dict]
_GetObjectReturn = _t.Union[_t.Optional[_WaapiValue], _t.Tuple[_t.Optional[_WaapiValue], ...]]
_CreateObjectsMethod = _t.Union[_t.Literal['wide'], _t.Literal['deep']]
_StrOrSeqOfStr = _t.Union[str, _t.Sequence[str]]


def _check_client(client: _w.WaapiClient) -> bool:
    return client is not None and client.is_connected()


def _check_fields(obj: dict, *fields: str) -> bool:
    if not isinstance(obj, dict):
        return False
    return all(f in obj for f in fields)


def _check_get_ret(ret: _t.Dict[str, _t.Any]) -> bool:
    return _check_fields(ret, 'return') and len(ret['return']) > 0


def _iter_dict_depth(d: _t.Dict[_t.Any, _t.Any], key: _t.Any) -> _t.Iterator:
    if d is None:
        return
    root = d
    yield root
    while key in root:
        root = root[key]
        yield root


def _get_filename(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def _is_seq(x):
    return hasattr(x, '__iter__')


def _ensure_str_list(x: _StrOrSeqOfStr, ignore=None) -> _t.List[str]:
    if ignore is not None and x == ignore:
        return x

    if isinstance(x, str):
        return [x]
    elif _is_seq(x):
        return [i for i in x]
    else:
        raise ValueError("Invalid type of argument 'x'")


def _is_any_val_none(*args):
    return not all(args)


# ------------------------------------------

def get_object(client: _w.WaapiClient,
               guid_or_path: str,
               properties: _StrOrSeqOfStr = None) -> _GetObjectReturn:
    """
    Get properties of an object in Wwise project.
    Please note, property names can be prefixed with '@' symbol,
    please refer to 'Return Options' documentation:
    https://www.audiokinetic.com/library/edge/?source=SDK&id=waapi_query.html#waapi_query_return

    :param client: WAAPI client, it should be connected.
    :param guid_or_path: Either an ID or a path of a Wwise object.
    :param properties: Either a string or a list of strings representing
                       names of properties value of which should be retrieved.
    :return: A tuple of property values corresponding to `properties` argument.

    Example:
    .. code-block:: python
       from waapi import WaapiClient
       from waapi_helpers import *

       with WaapiClient() as client:
           guid, = get_object(client, '\\Actor-Mixer Hierarchy\\Default Work Unit', 'id')
           print('ID of Default Work Unit is', guid)
           obj_name, obj_type get_object(client, guid, ['name', 'type'])
           print('Its name and type are', obj_name, obj_type)
    """

    if properties is None:
        properties = ['id']

    assert _check_client(client)
    assert guid_or_path is not None

    props = _ensure_str_list(properties)

    is_path = guid_or_path.startswith('\\')
    from_key = 'path' if is_path else 'id'
    query = {'from': {from_key: [guid_or_path]}}

    ret = client.call(_c.core_object_get, query, options={'return': props})

    if _check_get_ret(ret):
        obj = ret['return'][0]
        return tuple(obj.get(p, None) for p in props)
    else:
        return tuple(None for _ in props)


def get_name_of_guid(client: _w.WaapiClient, guid: str) -> _t.Optional[str]:
    """
    Get name of an object with specified ID

    :param client: WAAPI client, it should be connected.
    :param guid: A GUID string of an object, e.g. '{7C4789C3-1D8B-40C7-B3D9-2118F3582D5A}
    :return: A name of an object, or None if the object doesn't exist.

    Example:
    .. code-block:: python
       from waapi import WaapiClient
       from waapi_helpers import *

       with WaapiClient() as client:
           guid = get_guid_of_path(client, '\\Actor-Mixer Hierarchy\\Default Work Unit')
           name = get_name_of_guid(client, guid)
           print('Name of Default Work Unit is', name)
    """
    value, = get_object(client, guid, ['name'])
    return value


def get_path_of_guid(client: _w.WaapiClient, guid: str) -> _t.Optional[str]:
    """
    Get path of an object with specified ID

    :param client: WAAPI client, it should be connected.
    :param guid: A GUID string of an object, e.g. '{7C4789C3-1D8B-40C7-B3D9-2118F3582D5A}
    :return: Path of an object with specified ID, or None if the object doesn't exist.

    Example:
    .. code-block:: python
       from waapi import WaapiClient
       from waapi_helpers import *

       with WaapiClient() as client:
           guid = get_guid_of_path(client, '\\Actor-Mixer Hierarchy\\Default Work Unit')
           name = get_name_of_guid(client, guid)
           print('Name of Default Work Unit is', name)
    """
    value, = get_object(client, guid, ['path'])
    return value


def get_guid_of_path(client: _w.WaapiClient, path: str) -> _t.Optional[str]:
    """
    Get ID of an object at specified path.

    :param client: WAAPI client, it should be connected.
    :param path: The path of an object.
    :return: ID of an object specified by path, or None if the object doesn't exist.

    Example:
    .. code-block:: python
       from waapi import WaapiClient
       from waapi_helpers import *

       with WaapiClient() as client:
           guid = get_guid_of_path(client, '\\Actor-Mixer Hierarchy\\Default Work Unit')
           print('The ID of Default Work Unit is', name)
    """
    value, = get_object(client, path, ['id'])
    return value


def get_name_of_path(client: _w.WaapiClient, path: str) -> _t.Optional[str]:
    """
    Get name of an object with specified path.

    :param client: WAAPI client, it should be connected.
    :param path: A path of an object.
    :return: A name of an object, or None if the object doesn't exist.

    Example:
    .. code-block:: python
       from waapi import WaapiClient
       from waapi_helpers import *

       with WaapiClient() as client:
           name = get_name_of_path(client, '\\Actor-Mixer Hierarchy\\Default Work Unit')
           print('Name of Default Work Unit is', name)
    """
    value, = get_object(client, path, ['name'])
    return value


def get_parent_guid(client: _w.WaapiClient, obj_guid) -> _t.Optional[str]:
    """
    Get ID of the object's parent.

    :param client: WAAPI client, it should be connected.
    :param obj_guid: An ID of a child object.
    :return: An ID of a parent object.

    Example:
    .. code-block:: python
       from waapi import WaapiClient
       from waapi_helpers import *

       with WaapiClient() as client:
           child_guid = get_guid_of_path(client, '\\Actor-Mixer Hierarchy\\Default Work Unit')
           parent_guid = get_parent_guid(client, child_guid)
           print('ID of Actor-Mixer Hierarchy is', name)
    """
    query = {
        'from': {'id': [obj_guid]},
        'transform': [{'select': ['parent']}]
    }
    ret = client.call(_c.core_object_get, query, options={'return': ['id']})
    if _check_get_ret(ret):
        return ret['return'][0]['id']
    else:
        return None


def get_property_names(client: _w.WaapiClient, obj_guid: str) -> _t.Sequence[str]:
    """
    Get a sequence of property names available for an object.

    :param client: WAAPI client, it should be connected.
    :param obj_guid: An ID of the object.
    :return: A sequence of property names.

    Example:
    .. code-block:: python
       from waapi import WaapiClient
       from waapi_helpers import *

       with WaapiClient() as client:
           guid = get_guid_of_path(client, '\\Actor-Mixer Hierarchy\\Default Work Unit')
           prop_names = get_property_names(client, guid)
           print('Default Work Unit has the following properties:', prop_names)
    """
    ret = client.call(_c.core_object_get_prop_and_ref_names,
                      {'object': obj_guid})
    if _check_fields(ret, 'return'):
        return ret['return']
    else:
        return []


def get_property_value(client: _w.WaapiClient,
                       guid_or_path: str,
                       property_name: str) -> _t.Optional[_WaapiValue]:
    """
    Get an object's property value.
    Please note, property names can be prefixed with '@' symbol,
    please refer to 'Return Options' documentation:
    https://www.audiokinetic.com/library/edge/?source=SDK&id=waapi_query.html#waapi_query_return

    :param client: WAAPI client, it should be connected.
    :param guid_or_path: An ID or a path of the object.
    :param property_name: A name of the property.
    :return: A value of the property, or None when the object or the property doesn't exist.

    Example:
    .. code-block:: python
       from waapi import WaapiClient
       from waapi_helpers import *

       with WaapiClient() as client:
           master_bus_guid = get_bus_guid_from_name(client, 'Master Audio Bus')
           bus_volume = get_property_value(client, master_bus_guid, '@BusVolume')
           print('Master bus volume is', bus_volume)
    """
    value, = get_object(client, guid_or_path, properties=[property_name])
    return value


def get_bus_guid_from_name(client: _w.WaapiClient,
                           bus_name: str) -> _t.Optional[str]:
    """
    Get ID of a bus with specified name.

    :param client: WAAPI client, it should be connected.
    :param bus_name: Bus name.
    :return: A bus ID, or None when bus with specified name doesn't exist.

    Example:
    .. code-block:: python
       from waapi import WaapiClient
       from waapi_helpers import *

       with WaapiClient() as client:
           guid = get_bus_guid_from_name(client, 'Master Audio Bus')
           print('Master bus ID is', guid)
    """
    for guid, name in walk_wproj(client, '\\Master-Mixer Hierarchy', ['id', 'name'], ['Bus']):
        if name == bus_name:
            return guid
    return None


def set_property_value(client: _w.WaapiClient,
                       obj_guid_or_path: str,
                       property_name: str,
                       value: _WaapiValue):
    """
    Set a property of an object to the specified value.

    :param client: WAAPI client, it should be connected.
    :param obj_guid_or_path: An ID or a path of the modified object.
    :param property_name: A name of the property.
    :param value: A value to assign to the property.
    """
    if value is None:
        return
    client.call(_c.core_object_set_property, {'object': obj_guid_or_path,
                                              'property': property_name,
                                              'value': value})


def set_reference(client: _w.WaapiClient,
                  obj_guid_or_path: str,
                  reference_name: str,
                  ref_guid_or_path: str):
    """
    Set a property of an object to the specified value.

    :param client: WAAPI client, it should be connected.
    :param obj_guid_or_path: An ID or a path of the object being modified.
    :param reference_name: A name of the reference.
    :param ref_guid_or_path: An ID of or a path to the referenced object.
    """
    if ref_guid_or_path is None:
        return
    client.call(_c.core_object_set_reference, {'object': obj_guid_or_path,
                                               'reference': reference_name,
                                               'value': ref_guid_or_path})


def does_object_exist(client: _w.WaapiClient, guid_or_path: str) -> bool:
    """
    Check if an object exists. The function temporarily suppresses
    WAMP logging regarding non-existent objects.

    :param client: WAAPI client, it should be connected.
    :param guid_or_path: Either an ID or a path of a Wwise object.
    :return: True if the object exists, False otherwise.
    """
    old_log_level = suppress_waapi_logs()
    guid, = get_object(client, guid_or_path, properties='id')
    set_waapi_log_level(old_log_level)
    return guid is not None


def get_wproj_path(client: _w.WaapiClient) -> str:
    """
    Returns a path to the Wwise project, based on file path of Default Work Unit.
    Sometimes it's more convenient to do through WAAPI than through argv.

    :param client: WAAPI client, it should be connected.
    :return: A path to the Wwise project.
    """

    wwu_path, = get_object(client, '\\Actor-Mixer Hierarchy\\Default Work Unit',
                           properties='filePath')
    return os.path.abspath(os.path.realpath(wwu_path))


# ------------------------------------------

def _walk_depth_first(client, start, props, ret_props, types):
    query = {
        'from': {'path': [start]} if start.startswith('\\') else {'id': [start]},
        'transform': [{'select': ['children']}]
    }

    ret = client.call(_c.core_object_get, query, options={'return': props})
    if not _check_get_ret(ret):
        return

    for obj in ret['return']:
        if types == 'any' or obj['type'] in types:
            yield tuple(obj.get(p, None) for p in ret_props)
        yield from _walk_depth_first(client, obj['id'], props, ret_props, types)


def walk_wproj(client: _w.WaapiClient,
               start_guids_or_paths: _StrOrSeqOfStr,
               properties: _StrOrSeqOfStr = None,
               types: _StrOrSeqOfStr = 'any') -> _t.Iterator[_t.Tuple[_WaapiValue]]:
    """
    Walk through descendants of an object and yield their properties.

    :param client: WAAPI client, it should be connected.
    :param start_guids_or_paths: Either an ID or a path where iteration starts. If a list is passed,
                                 the iterator will walk descendants of each object in the list.
                                 Can be either a str or a list of str.
    :param properties: A list of property names. Their values will be yielded as tuples. Default is ['id'].
                       Can be either a str or a list of str.
    :param types: A list of object types which properties will be yielded during walk. Default is 'any'.
                  Can be either a str or a list of str.
    :return: A tuple of property values in the order specified by the 'properties' argument.
             If a property doesn't exist, its corresponding value will be 'None'.

    Example:
    .. code-block:: python
       from waapi import WaapiClient
       from waapi_helpers import *

       with WaapiClient() as client:
           for guid, name in walk_wproj(client, '\\Actor-Mixer Hierarchy',
                                        properties=['id', 'name'], types='any'):
              print('Object', name, 'has ID of', guid)
    """
    if properties is None:
        properties = ['id']

    if not _check_client(client):
        raise ValueError('Waapi client is none or disconnected')
    if _is_any_val_none(start_guids_or_paths, types):
        return ValueError('start_guids_or_path and types cannot be None')

    start_list = _ensure_str_list(start_guids_or_paths)
    props = _ensure_str_list(properties)
    req_types = _ensure_str_list(types, 'any')

    ret_props = copy.copy(props)
    for p in 'id', 'type':
        if p not in props:
            props.append(p)

    for start in start_list:
        yield from _walk_depth_first(client, start, props, ret_props, req_types)


# ------------------------------------------

def _create_objects__deep(client, parent, names, types, on_name_conflict):
    query = {
        'parent': parent,
        'onNameConflict': on_name_conflict
    }

    first = True
    root = query
    for obj_name, obj_type in zip(names, types):
        if first:
            first = False
        else:
            root['children'] = [{}]
            root = root['children'][0]
        root['name'] = obj_name
        root['type'] = obj_type

    ret = client.call(_c.core_object_create, query)
    if _check_fields(ret, 'id'):
        return [obj['id'] for obj in _iter_dict_depth(ret, 'children') if 'id' in obj]
    else:
        return []


def _create_objects__wide(client, parent, names, types, on_name_conflict):
    created_guids = []
    for obj_name, obj_type in zip(names, types):
        obj = client.call(_c.core_object_create, {
            'parent': parent,
            'onNameConflict': on_name_conflict,
            'name': obj_name,
            'type': obj_type
        })

        if _check_fields(obj, 'id'):
            created_guids.append(obj['id'])
        else:
            created_guids.append(None)
    return created_guids


def create_objects(client: _w.WaapiClient,
                   parent_guid_or_path: str,
                   names: _StrOrSeqOfStr,
                   types: _StrOrSeqOfStr,
                   method: _CreateObjectsMethod = 'wide',
                   on_name_conflict: _OnNameConflict4 = 'merge') -> _t.Sequence[_t.Optional[str]]:
    """
    Create objects with specified names and types under some parent.

    :param client: WAAPI client, it should be connected.
    :param parent_guid_or_path: Either an ID or a path of a parent object.
    :param names: A list of new object names.
    :param types: A list of new object types.
    :param method: If 'wide', new objects will be placed directly under parent object.
                   If 'deep', new objects will form deep hierarchy placing one as a child of another.
                   Default is 'wide.
    :param on_name_conflict: Name conflict mode. Can be 'rename', 'replace', 'fail', or 'merge'.
                             Default is 'merge'. For more info please refer to the WAAPI documentation:
                             https://www.audiokinetic.com/library/edge/?source=SDK&id=waapi_import.html
    :return: A sequence of object IDs that were created. If an object was not created, None will appear
             instead of its ID. If the whole operation fails, an empty sequence will be returned.

    Example:
    .. code-block:: python
       from waapi import WaapiClient
       from waapi_helpers import *

       with WaapiClient() as client:
           wide_guids = create_objects(client, '\\Actor-Mixer Hierarchy\\Default Work Unit',
                                       names=['Folder_01', 'Folder_02'], types=['Folder', 'Folder'],
                                       method='wide')
           deep_guids = create_objects(client, '\\Actor-Mixer Hierarchy\\Default Work Unit',
                                       names=['Folder_03', 'Folder_04'], types=['Folder', 'Folder'],
                                       method='deep')
           # please open your Wwise project to see the changes
    """
    assert _check_client(client)

    req_names = _ensure_str_list(names)
    req_types = _ensure_str_list(types)
    assert len(req_names) == len(req_types)

    if len(names) == 0:
        return []

    if method == 'wide':
        return _create_objects__wide(client, parent_guid_or_path, req_names, req_types, on_name_conflict)
    elif method == 'deep':
        return _create_objects__deep(client, parent_guid_or_path, req_names, req_types, on_name_conflict)
    else:
        raise ValueError("create_objects method be either 'wide' or 'deep'")


def get_bank_inclusions_guids(client: _w.WaapiClient, bank: str) -> _t.Sequence[str]:
    """
    Get IDs of objects included in to specified bank.

    :param client: WAAPI client, it should be connected.
    :param bank: An ID, a path, or a name of a bank.
    :return: Sequence of IDs of the included objects.
             Empty sequence if the operation failed.
    """
    ret = client.call(_c.core_soundbank_get_inclusions, {'soundbank': bank})
    if _check_fields(ret, 'inclusions'):
        return [incl['object'] for incl in ret['inclusions']]
    else:
        return []


def set_bank_inclusions(client: _w.WaapiClient,
                        bank_guid: str,
                        inclusion_guids: _t.Sequence[str],
                        inclusion_op: _InclusionOperation = 'replace',
                        inclusion_filter: _t.Sequence[str] = None):
    """
    Set sound bank inclusions.

    Explanation of inclusion_op and inclusion_filter parameters is given
    in the WAAPI documentation:
    https://www.audiokinetic.com/library/edge/?source=SDK&id=ak_wwise_core_soundbank_setinclusions.html

    :param client: WAAPI client, it should be connected.
    :param bank_guid: A bank ID.
    :param inclusion_guids: A sequence of IDs to include into the bank.
    :param inclusion_op: Inclusion operation.
                         Can be 'add', 'remove', or 'replace'. Default is 'replace'.
    :param inclusion_filter: Inclusion filter. Default is ['events', 'structures', 'media'].
    """
    if inclusion_filter is None:
        inclusion_filter = ['events', 'structures', 'media']
    client.call(_c.core_soundbank_set_inclusions,
                {'operation': inclusion_op, 'soundbank': bank_guid,
                 'inclusions': [{'object': guid, 'filter': inclusion_filter}
                                for guid in inclusion_guids]})


def _copy_or_move_object(client: _w.WaapiClient,
                         uri: str,
                         copy_from: str,
                         new_parent: str,
                         on_name_conflict: _OnNameConflict3 = 'fail') -> _t.Optional[str]:
    assert _check_client(client)

    ret = client.call(uri, {'object': copy_from,
                            'parent': new_parent,
                            'onNameConflict': on_name_conflict})

    if _check_fields(ret, 'id'):
        return ret['id']
    else:
        return None


def copy_object(client: _w.WaapiClient,
                copy_from: str,
                new_parent: str,
                on_name_conflict: _OnNameConflict3 = 'fail') -> _t.Optional[str]:
    """
    Copies an object some new parent.

    :param client: WAAPI client, it should be connected.
    :param copy_from: An ID of the object to copy.
    :param new_parent: An ID of a parent to place a copy of the object.
    :param on_name_conflict: Name conflict strategy. Can be 'rename', 'replace', or 'fail'. Default is 'fail'.
    :return: An ID of the new object, or 'None' if the operation failed.
    """
    return _copy_or_move_object(client, _c.core_object_copy,
                                copy_from, new_parent, on_name_conflict)


def move_object(client: _w.WaapiClient,
                obj_guid: str,
                new_parent: str,
                on_name_conflict: _OnNameConflict3 = 'fail') -> _t.Optional[str]:
    """
    Moves an object some new parent.

    :param client: WAAPI client, it should be connected.
    :param obj_guid: An ID of the object to move.
    :param new_parent: An ID of a new parent of the object.
    :param on_name_conflict: Name conflict strategy. Can be 'rename', 'replace', or 'fail'. Default is 'fail'.
    :return: An ID of the object, or 'None' if the operation failed.
    """
    return _copy_or_move_object(client, _c.core_object_move,
                                obj_guid, new_parent, on_name_conflict)


def delete_object(client: _w.WaapiClient, obj_guid: str):
    """
    Deletes an object

    :param client: WAAPI client, it should be connected.
    :param obj_guid: An ID of the object to move.
    """
    client.call(_c.core_object_delete, {'object': obj_guid})


def copy_properties(client: _w.WaapiClient,
                    copy_from_guid: str,
                    assign_to_guid: str):
    """
    Copies properties from one object to another.
    TODO: this function does not currently copy references.

    :param client: WAAPI client, it should be connected.
    :param copy_from_guid: An ID of the object to copy properties from.
    :param assign_to_guid: An ID of the object to assign properties to.
    """
    src_names = set(get_property_names(client, copy_from_guid))
    target_names = set(get_property_names(client, assign_to_guid))

    for prop in src_names.intersection(target_names):
        v = get_property_value(client, copy_from_guid, prop)
        is_reference = isinstance(v, dict)
        if not is_reference:
            set_property_value(client, assign_to_guid, prop, v)


# ------------------------------------------

def import_audio(client: _w.WaapiClient,
                 parent_guid: str,
                 wav_files: _t.Sequence[str],
                 import_operation: _ImportOperation = 'useExisting',
                 orig_subfolder: str = '',
                 is_voice: bool = False):
    """
    Imports audio files into the project and places them under
    specified parent either as 'Sound' or 'Voice'.

    TODO: support voice language.

    :param client: WAAPI client, it should be connected.
    :param parent_guid: An ID of the object where to import audio files.
    :param wav_files: A list of paths to the .wav files.
    :param import_operation: Import operation. Can be 'createNew', 'useExisting',
                             or 'replaceExisting'. Default is 'useExisting'.
    :param orig_subfolder: A sub-folder in 'Originals' to copy .wav files to.
    :param is_voice: If True, a 'Voice' object will be created.
                     If False, a 'Sound' object will be created.
    """
    tag = '<Voice>' if is_voice else '<Sound>'  # haven't tested this one actually
    query = {
        'default': {
            'importLocation': parent_guid,
            'originalsSubFolder': orig_subfolder,
        },
        'importOperation': import_operation,
        'imports': [{
            'audioFile': wav,
            'objectPath': tag + _get_filename(wav)
        } for wav in wav_files]
    }
    client.call(_c.core_audio_import, query)


# ------------------------------------------

def begin_undo_group(client: _w.WaapiClient):
    """
    Begin undo group.

    :param client: WAAPI client, it should be connected.
    """
    client.call(_c.core_undo_begin_group)


def end_undo_group(client: _w.WaapiClient, display_name: str):
    """
    End undo group.

    :param client: WAAPI client, it should be connected.
    :param display_name: A display name for this undo group.
    """
    client.call(_c.core_undo_end_group, {'displayName': display_name})


def cancel_undo_group(client: _w.WaapiClient):
    """
    Cancel undo group.

    :param client: WAAPI client, it should be connected.
    """
    client.call(_c.core_undo_cancel_group)


def perform_undo(client: _w.WaapiClient):
    """
    Perform undo operation in the Wwise project.

    :param client: WAAPI client, it should be connected.
    """
    client.call(_c.ui_commands_execute, {'command': 'Undo'})


def perform_redo(client: _w.WaapiClient):
    """
    Perform redo operation in the Wwise project.

    :param client: WAAPI client, it should be connected.
    """
    client.call(_c.ui_commands_execute, {'command': 'Redo'})


# ------------------------------------------

def get_waapi_log_level() -> int:
    """
    Return current WampClientAutobahn log level.

    :return: Log level.
    """
    return _w.WampClientAutobahn.logger.getEffectiveLevel()


def set_waapi_log_level(level: int):
    """
    Set WampClientAutobahn log level
    """
    return _w.WampClientAutobahn.logger.setLevel(level)


def suppress_waapi_logs(with_level: int = 1000) -> int:
    """
    Set WampClientAutobahn log level and return previous level.
    Supposed to be used to temporarily disable WAAPI logs,
    e.g. to prevent extensive logging under certain operations.

    :param with_level: New log level. Default is 1000.
    :return: Previous log level.
    """
    old_level = get_waapi_log_level()
    set_waapi_log_level(with_level)
    return old_level
