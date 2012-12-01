#!/bin/sh

HOST="${HOST:-root@10.35.1.113}"

mytmp="$(mktemp -d)"
cleanup() {
	rm -fr "${mytmp}"
}
trap cleanup 0

make -C "$(dirname $0)/.."  install DESTDIR="${mytmp}" &&
	( tar -hc -C "${mytmp}"/usr/local/share/ovirt-host-deploy/interface-3 . && cat) | \
		ssh ${HOST} '( dest=/tmp/xxx && rm -fr "${dest}" && mkdir -p "${dest}" && \
			python -c "import sys, tarfile; tarfile.open(fileobj=sys.stdin, mode=\"r|\").extractall(path=\"${dest}\")" && \
			OTOPI_DEBUG=1 "${dest}"/setup "DIALOG/customization=bool:True '"$*"'" )'
echo "exit $?"
