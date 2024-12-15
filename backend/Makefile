
.PHONY: clean
clean:
	rm -rf dist

.PHONY: build
build: build-frontend
	python -m build

.PHONY: build-frontend
build-frontend:
	cd ../frontend && npm run build
	rm -rf ./kfe/resources/frontend_build
	cp -r ../frontend/build ./kfe/resources/frontend_build

.PHONY: run
run:
	python -m kfe.main
