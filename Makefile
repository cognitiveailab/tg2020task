TABLESTORE := expl-tablestore-export-2020-02-17-123232
WORLDTREE := $(TABLESTORE)-traindevetest.zip

evaluate: predict-tfidf.txt
	./evaluate.py --gold=$(TABLESTORE)/questions.dev.tsv $<

submission: predict-tfidf-test.zip

predict-tfidf%.zip: predict-tfidf%.txt
	rm -f $@
	$(eval TMP := $(shell mktemp -d))
	ln -sf $(CURDIR)/$< $(TMP)/predict.txt
	zip -j $@ $(TMP)/predict.txt
	rm -rf $(TMP)

predict-tfidf-test.txt:
	./baseline_tfidf.py $(TABLESTORE)/tables $(TABLESTORE)/questions.test.tsv > $@

predict-tfidf.txt:
	./baseline_tfidf.py $(TABLESTORE)/tables $(TABLESTORE)/questions.dev.tsv > $@

dataset: $(WORLDTREE)
	unzip -o $<

$(WORLDTREE): worldtree_corpus.sha256
	@echo 'Please note that this distribution is still subject to the terms set forth in the included license.'
	@echo 'See the full license for specific details: EULA AI2 Mercury Dataset 01012018.docx'
	curl -sL -o "$@" 'http://cognitiveai.org/dist/$(WORLDTREE)'
	sha256sum -c "$<"
