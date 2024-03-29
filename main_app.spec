# -*- mode: python ; coding: utf-8 -*-

import sys
sys.setrecursionlimit(5000)

block_cipher = None


added_files = [
         ( 'C:\\ProgramData\\Anaconda3\\envs\\scopefoundry\\Lib\\site-packages\\ScopeFoundry\\base_microscope_app_mdi.ui', 'ScopeFoundry' ),
         ( 'C:\\ProgramData\\Anaconda3\\envs\\scopefoundry\\Lib\\site-packages\\ScopeFoundry\\base_microscope_app.ui', 'ScopeFoundry' ),
         ( 'JVMeasurement_ui.ui','.')
         ]

a = Analysis(['main_app.py'],
             pathex=['C:\\Users\\Labuser\\Documents\\GitHub\\KeithleyJVGUI'],
             binaries=[],
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='main_app',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          uac_admin= True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='main_app')
