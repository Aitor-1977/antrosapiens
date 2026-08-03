# Conectores de ingesta Capa 0 (100% gratuitos; leen config de .env).
# Operación autónoma: sin variables, cada receta barre sus listas por defecto.
PYTHON ?= python3
QUERY ?=
FEED ?=
LIMITE ?= 25
URL ?=
ORG ?=
LANG ?= es

.PHONY: help install test noticias youtube
help:
	@echo "make install                       # instala requirements"
	@echo "make test                          # corre las pruebas"
	@echo "make noticias                      # autónomo: consultas por defecto"
	@echo "make noticias QUERY=\"fintech México ronda\""
	@echo "make noticias FEED=<URL_RSS>"
	@echo "make youtube                       # autónomo: cola HD_INGESTA_DEFAULT_VIDEOS"
	@echo "make youtube URL=<video> ORG=\"Acme\" LANG=es"

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

noticias:
	$(PYTHON) -m hd_scraper.ingesta noticias $(if $(QUERY),--query "$(QUERY)") $(if $(FEED),--feed "$(FEED)") --limite "$(LIMITE)"

youtube:
	$(PYTHON) -m hd_scraper.ingesta youtube $(if $(URL),--url "$(URL)") $(if $(ORG),--org "$(ORG)") --lang "$(LANG)"
