source bin/activate
mkdir -p docs
mkdir -p docs/preds
rm jpred.db
rm -r docs/j*.html
rm docs/users.html
rm -r docs/preds/*.html
./create_db.sh
./jpred.py docs/j1.html columns/j1.cols
./jpred.py docs/j2.html columns/j2.cols
./jpred.py docs/j3.html columns/j3.cols
./jpred_users.py
cp assets/favicons/*.png docs
cp assets/favicons/*.ico docs
cp assets/favicons/site.webmanifest docs
