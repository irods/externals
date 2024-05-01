#!/bin/bash
# quick n dirty script to make a patch

diff_out=$(mktemp --tmpdir newpatch.XXXXXX.diff)

# generate diff
diff -pru "$@" > "${diff_out}"

if ! [ -s "${diff_out}" ]; then
	# diff output is empty. exit.

	# remove diff output
	rm -f "${diff_out}"

	exit 0
fi

# diffstat
diffstat_out=$(mktemp --tmpdir newpatch.XXXXXX.stat)
diffstat -Kp1 < "${diff_out}" > "${diffstat_out}"

#git_username="$(git config --get user.name)"
#git_email="$(git config --get user.email)"
#if [[ ! ( -z "${git_username}" || -z "${git_email}" ) ]]; then
#	echo "From: ${git_username} <${git_email}>"
#fi

#patch_date="$(date --rfc-email --reference="${diff_out}")"
#echo "Date: ${patch_date}"

# print patch
echo "---"
cat "${diffstat_out}"
echo
cat "${diff_out}"
echo "-- "
echo

# remove diffstat output
rm -f "${diff_out}" "${diffstat_out}"
