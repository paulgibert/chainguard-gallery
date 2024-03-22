.PHONY: list-official
list-official:
	@python ls_docker.py "" \
		--image-filter official \
		--tags latest

.PHONY: list-rapidfort
list-rapidfort:
	@python ls_docker.py rapidfort \
		--repository-prefix rapidfort \
		--tags latest

.PHONY: list-canonical
list-canonical:
	@python ls_docker.py canonical \
		--repository-prefix ubuntu \
		--tags "latest edge"

.PHONY: list-bitnami
list-bitnami:
	@python ls_docker.py bitnami \
		--repository-prefix bitnami \
		--tags edge

.PHONY: list-mcr-chiselled
list-mcr-chiselled:
	@python ls_mcr_chiselled.py