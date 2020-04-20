echo "> 현재 구동중인 애플리케이션 pid 확인"

CURRENT_PID=$(pgrep -f lightcomics)

echo "$CURRENT_PID"

if [ -z $CURRENT_PID ]; then
    echo "> Not Running!"
else
    echo "> kill -2 $CURRENT_PID"
    kill -9 $CURRENT_PID
    sleep 1
    echo "TURN OFF COMPLETE"
fi


echo "> 현재 구동중인 애플리케이션 pid 확인"

CURRENT_PID=$(pgrep -f lightcomics)

echo "$CURRENT_PID"

if [ -z $CURRENT_PID ]; then
    echo "> Not Running!"
else
    echo "> kill -2 $CURRENT_PID"
    kill -9 $CURRENT_PID
    sleep 1
    echo "TURN OFF COMPLETE"
fi
