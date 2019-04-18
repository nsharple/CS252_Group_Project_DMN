all: git-commit

.PHONY: git-commit
git-commit:
	git checkout Nolan
	git add *
	git commit
	git push origin Nolan

