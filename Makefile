TABLESTORE := expl-tablestore-export-2020-02-17-123232
WORLDTREE := tg2020task-dataset.zip

evaluate: predict-tfidf-dev.txt
	./evaluate.py --gold=$(TABLESTORE)/questions.dev.tsv $<

submission: predict-tfidf-test.zip

predict-tfidf-%.zip: predict-tfidf-%.txt
	rm -f $@
	$(eval TMP := $(shell mktemp -d))
	ln -sf $(CURDIR)/$< $(TMP)/predict.txt
	zip -j $@ $(TMP)/predict.txt
	rm -rf $(TMP)

predict-tfidf-%.txt:
	./baseline_tfidf.py $(TABLESTORE)/tables $(TABLESTORE)/questions.$*.tsv > $@

dataset: $(WORLDTREE)
	rm -rf $(TABLESTORE)
	unzip -o $<

SHA256CHECK := $(shell type -p sha256sum || echo shasum -a 256)

$(WORLDTREE): worldtree_corpus.sha256
	@echo 'Please note that this distribution is subject to the terms set in the license:'
	@echo 'http://cognitiveai.org/explanationbank/'
	curl -sL -o "$@" 'http://cognitiveai.org/dist/$(WORLDTREE)'
	$(SHA256CHECK) -c "$<"

clean:
	rm -rf $(TABLESTORE)
	rm -fv predict*.txt predict*.zip

distclean: clean
	rm -fv $(WORLDTREE)
