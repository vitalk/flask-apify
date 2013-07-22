help:
	@echo "Please use \`make <target>\` where <target> is one of"
	@echo " clean       to cleanup build directory"
	@echo " test        to run the test suite"
	@echo " install     to install package"


clean:
	@rm -rf *.egg{,-info}
	@find . -name *.py[co] -delete


test:
	@py.test tests


install:
	@pip install -r requirements.txt
