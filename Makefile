.PHONY: demo test clean build dev

# Run complete demo
demo:
	./demo/reset.sh && ./demo/seed.sh && ./demo/run-demo.sh

# Run all tests
test:
	python tests/test_golden.py

# Reset demo state
reset:
	./demo/reset.sh

# Benchmark
benchmark:
	./demo/benchmark.sh

# Start backend
api:
	cd apps/api && uvicorn main:app --reload --port 8000

# Start frontend
web:
	cd apps/web && npm run dev

# Build frontend
build:
	cd apps/web && npm run build

# Install Python dependencies
install:
	pip install fastapi uvicorn pydantic mcp

# Generate documents
docs:
	python documents/generate_docs.py

# Full clean
clean:
	rm -rf apps/web/dist
	rm -f .lockstep/runs/*.json
	rm -f .lockstep/investigation.log
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
