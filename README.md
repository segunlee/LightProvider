# NOT SUPPORT ANYMORE
해당 프로젝트는 더 이상 지원하지 않습니다. 새로운 LightProvider를 이용하세요
[이동하기](https://github.com/segunlee/LightProviderNest)


# LightProvider - Python-based LightComics Server
파이선3 베이스로 작성된 LightComics 압축파일 스트리밍 서버입니다.




## 필요 패키지
```
Flask
Pillow
requests
Tkinter
chardet
rarfile
```



## 지원

ZIP, CBZ 파일만 지원합니다. (Windows, MacOS)
Linux or SynologNAS는 RAR, CBR 파일도 지원됩니다.




## How To Run?

원도우: https://github.com/segunlee/LightProvider/releases/download/1.0.3/LightProvider.exe

맥 OSX: https://github.com/segunlee/LightProvider/releases/download/1.0.3/LightProvider.app.zip

시놀로지 NAS: [메뉴얼 보기](/howtosetupindocker.md)

리눅스:
실행파일 lightcomics.py
설정파일 lightcomics.json

```
{
    "ROOT": "/home/user/ec2-user/manhwa",
    "PORT": 12370,
    "HOST": "0.0.0.0",
    "PASSWORD": "TEST"
}
```

```
python lightcomics.py &
```



## TODO

- [O] Support Linux base OS 
- [O] Support Windows OS
- [O] Support Mac OSX
