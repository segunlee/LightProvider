# 베타 서비스중


# LightProvider - Python-based LightComics Server
파이선3 베이스로 작성된 LightComics 압축파일 스트리밍 서버입니다.

현재 테스트플라이트 버전에 기능이 포함되어 있습니다.




## 필요 패키지
```
Flask
Pillow
requests
Tkinter
```

## 지원
현재 zip 파일만 지원합니다.


## How To Run?

원도우: https://github.com/segunlee/LightProvider/releases/download/1.0.3/LightProvider.exe

맥 OSX: https://github.com/segunlee/LightProvider/releases/download/1.0.3/LightProvider.zip

리눅스:
실행파일 lightcomics.py
설정파일 lightcomics.json
```
{
  "ROOT": "/home/user/ec2-user/manhwa",
  "PORT": 8909,
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
