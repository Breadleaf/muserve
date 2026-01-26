root_dir=$(git rev-parse --show-toplevel)
dirs=(app  auth  auth_state  bootstrap_admin  database_handler  deploy storage_handler)
for dir in "${dirs[@]}"
do
	full_path="$root_dir/$dir"
	echo "Refreshing $full_path's environment..."
	cd $full_path
	make clean
	make setup
done
