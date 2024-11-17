
.PHONY: clean
clean:
	rm -rf dist

.PHONY: build
build:
	make build-frontend
	python -m build

.PHONY: build-frontend
build-frontend:
	cd ../frontend && npm run build
	cp -r ../frontend/build ./src/resources/frontend_build

.PHONY: run
run:
	python src/main.py
