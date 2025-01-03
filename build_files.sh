echo "Build has started"
python3.12 -m pip install -r requirements.txt
python3.12 manage.py collectstatic --noinput --clear
echo "Build ended successfully"
