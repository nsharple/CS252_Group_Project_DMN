all: git-commit

.PHONY: git-commit
git-commit:
	git checkout Nolan
	git add *
	git commit -m "Commit"
	git push origin Nolan

