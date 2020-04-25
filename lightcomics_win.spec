# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['lightcomics.py'],
             pathex=['C:\\Users\\LEESEGUN\\Documents\\LightProvider'],
             binaries=[],
             datas=[],
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
          a.binaries + [('icon.ico', 'C:\\Users\\LEESEGUN\\Documents\\LightProvider\\icon.ico', 'DATA')],
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
          console=False , icon='icon.ico')
