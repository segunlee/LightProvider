# LightProvider - Python-based LightComics Server
파이선3 베이스로 작성된 LightComics 압축파일 스트리밍 서버입니다.

## 필요 패키지
```
Flask
Pillow
```

## 지원
현재 zip 파일만 지원합니다.

## run
설정파일
```
{
  "ROOT": "z:/",
  "PORT": 8909,
  "HOST": "0.0.0.0",
  "PASSWORD": "TEST"
}
```

```
python lightcomics.py
```
