# PyComix - Python-based AirComix Server

This application can substitue the AricComix Server which supports Windows and OS X.

## Requirements
```
Flask
```

## Limitation
Only supports folder and zip file.

## run
Configuration file
```
{
  "ROOT": "z:/",
  "CONTENTS": "comics",
  "PORT": 31258,
  "HOST": "0.0.0.0",
  "PASSWORD": "TEST"
}
```

```
python comix.py
```
