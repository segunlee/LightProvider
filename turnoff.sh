echo "> Is Running?"

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


echo "> Is Running?"

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
