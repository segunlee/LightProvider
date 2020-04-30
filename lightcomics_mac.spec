# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['lightcomics.py'],
             pathex=['/Users/leesegun/Documents/GIT/LightProvider'],
             binaries=[],
             datas=[],
             hiddenimports=['pkg_resouces.py2_warn','pkg_resources.py2_warn', 'requests'],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='LightProvider',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
app = BUNDLE(exe,
             name='LightProvider.app',
             icon=None,
             bundle_identifier=None)
