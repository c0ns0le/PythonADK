# -*- coding: utf-8 -*-
import atexit
import ctypes
import inspect
import contextlib
import sys

DYNATRACE_AGENT_NAME = None
DYNATRACE_ADK_PATH   = None
DYNATRACE_AGENT_PATH = None
DYNATRACE_SERVER     = None
DYNATRACE_PORT       = None
DYNATRACE_API_NAME   = None
DYNATRACE_ADK        = None

# init should be called only once
# default values can be set here
def init(
    agentName = 'Python_Monitoring', 
    adkPath = 'C:/Program Files/Dynatrace/Dynatrace 6.5/adk/windows-x86-64/agent/lib64/dtadk.dll', 
    agentPath = 'C:/Program Files/Dynatrace/Dynatrace 6.5/agent/lib64/dtagent.dll', 
    server = 'localhost', 
    port = 9998, 
    apiName = 'Python'):
    global DYNATRACE_AGENT_NAME
    global DYNATRACE_ADK_PATH
    global DYNATRACE_AGENT_PATH
    global DYNATRACE_SERVER
    global DYNATRACE_PORT
    global DYNATRACE_API_NAME
    global DYNATRACE_ADK
    DYNATRACE_AGENT_NAME = agentName
    DYNATRACE_ADK_PATH = adkPath
    DYNATRACE_AGENT_PATH = agentPath
    DYNATRACE_SERVER = server
    DYNATRACE_PORT = port
    DYNATRACE_API_NAME = apiName
    DYNATRACE_ADK = ctypes.cdll.LoadLibrary('%s' % DYNATRACE_ADK_PATH)
    DYNATRACE_INITIALIZE()


def DYNATRACE_INITIALIZE():
    argc  = ctypes.c_int(3)
    _argv = ctypes.c_char_p * 3
    argv  = _argv(
        convertToBytes('--dt_agentlibrary=%s' % DYNATRACE_AGENT_PATH),
        convertToBytes('--dt_agentname=%s' % DYNATRACE_AGENT_NAME),
        convertToBytes('--dt_server=%s:%s' % (DYNATRACE_SERVER, DYNATRACE_PORT))
    )
    argv_p = ctypes.pointer(argv)
    if DYNATRACE_ADK.dynatrace_initialize(ctypes.byref(argc), ctypes.byref(argv_p)) != 0:
        raise Exception(u'failed to initialize')

def convertToBytes(str):
    if sys.version_info[0] < 3:
        return str
    else:
        return bytes(str, 'utf-8')

def DYNATRACE_START_SERVER_PUREPATH():
    DYNATRACE_ADK.dynatrace_start_server_purepath()

def DYNATRACE_END_SERVER_PUREPATH():
    DYNATRACE_ADK.dynatrace_end_server_purepath()

def DYNATRACE_UNINITIALIZE():
    DYNATRACE_ADK.dynatrace_uninitialize()

def DYNATRACE_GET_TAG_AS_STRING():
    buffer_size = 256
    c_buffer = ctypes.create_string_buffer(buffer_size)
    c_size   = ctypes.c_int(buffer_size)
    DYNATRACE_ADK.dynatrace_get_tag_as_string(ctypes.byref(c_buffer), ctypes.byref(c_size))
    return c_buffer.value


def DYNATRACE_SET_TAG_FROM_STRING(dynatrace_tag):
    DYNATRACE_ADK.dynatrace_set_tag_from_string(convertToBytes(dynatrace_tag))

# grab parameters from the stack frame
def _DYNATRACE_ENTER(entry_point, method=None, params_to_capture=None):
    framerecord = inspect.stack()[4]
    params = inspect.getargvalues(framerecord[0])
    paramNames = params[0]
    paramsVals = params[3]

    method_name = method or framerecord[3]
    dynatrace_method_id = DYNATRACE_ADK.dynatrace_get_method_id(convertToBytes(method_name), convertToBytes(framerecord[1]), framerecord[2]-1, convertToBytes(DYNATRACE_API_NAME), 0)
    dynatrace_serial_no = DYNATRACE_ADK.dynatrace_get_serial_no(dynatrace_method_id, entry_point)

    if not params_to_capture:
        for arg in paramNames:
            actParam = paramsVals.get(arg)
            argv_p = ctypes.create_string_buffer(convertToBytes(actParam))
            DYNATRACE_ADK.dynatrace_capture_string(dynatrace_serial_no, argv_p)
    else:
        for val in params_to_capture:
            val_buf = ctypes.create_string_buffer(convertToBytes(val))
            DYNATRACE_ADK.dynatrace_capture_string(dynatrace_serial_no, val_buf)

    dynatrace_serial_no = DYNATRACE_ADK.dynatrace_enter(dynatrace_method_id, dynatrace_serial_no)
    return dynatrace_method_id, dynatrace_serial_no


def DYNATRACE_ENTER(params_to_capture=None, method=None):
    return _DYNATRACE_ENTER(0,
                            params_to_capture=params_to_capture,
                            method=method)


def DYNATRACE_START_PUREPATH(params_to_capture=None, method=None):
    return _DYNATRACE_ENTER(1,
                            params_to_capture=params_to_capture,
                            method=method)


def DYNATRACE_EXIT(dynatrace_method_id, dynatrace_serial_no):
    DYNATRACE_ADK.dynatrace_exit(dynatrace_method_id, dynatrace_serial_no)


def DYNATRACE_LINK_CLIENT_PUREPATH_BY_STRING(synchronous, dynatrace_tag):
    DYNATRACE_ADK.dynatrace_link_client_purepath_by_string(synchronous, dynatrace_tag)


def DYNATRACE_START_SERVER_PUREPATH():
    DYNATRACE_ADK.dynatrace_start_server_purepath()


def DYNATRACE_END_SERVER_PUREPATH():
    DYNATRACE_ADK.dynatrace_end_server_purepath()

@contextlib.contextmanager
def sensor(params_to_capture=None, method=None):
    dynatrace_method_id, dynatrace_serial_no = DYNATRACE_ENTER(
        params_to_capture=params_to_capture, method=method)
    yield
    DYNATRACE_EXIT(dynatrace_method_id, dynatrace_serial_no)


@contextlib.contextmanager
def start_purepath(params_to_capture=None, method=None):
    dynatrace_method_id, dynatrace_serial_no = DYNATRACE_START_PUREPATH(
        params_to_capture=params_to_capture, method=method)
    yield
    DYNATRACE_EXIT(dynatrace_method_id, dynatrace_serial_no)
    DYNATRACE_END_SERVER_PUREPATH()


atexit.register(DYNATRACE_UNINITIALIZE)
