cd ..\\..\\CRF_train
crfsuite learn -m my.model select.train.crfsuite
crfsuite tag -qt -m my.model select.test.crfsuite
