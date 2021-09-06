#!/usr/bin/env python3
# coding: utf-8
# =========================================================================== #

# Download "machado" and "names", along with w/e they require
import nltk
nltk.download()

# --------------------------------------------------------------------------- #

from nltk.corpus import machado, names
from nltk.tokenize import RegexpTokenizer
from random import randint, choice, choices, sample, shuffle
import json
from cursos import curso_geral, curso_adjetivo, curso_especifico

# --------------------------------------------------------------------------- #

# Part 1 input generation (1/2)
tokenizer = RegexpTokenizer(r'\w+')

frases = [_.strip().replace('\n', ' ').replace('  ', ' ') for _ in machado.raw('romance/marm08.txt').split('.') if _.strip() and _ != '\n' and '\n\n' not in _]
frase = lambda: ((idx := randint(0, len(frases) - 1)), '_'.join(tokenizer.tokenize(frases[idx])))

print(f'Temos {len(frases)} frases.')

opts = {
    'I': lambda: ','.join([str((fr:=frase())[0]), fr[1] , str(len(fr[1]))]),
    'C': lambda: randint(0, len(frases) - 1),
}

# --------------------------------------------------------------------------- #

# Part 1 input generation (2/2)
with open('input.txt', 'w+') as foutput:
    for idx in range(1000):
        print(f'{(op:=choice(["I", "C"]))},{opts[op]()}', file=foutput)
    print('T', file=foutput)


# --------------------------------------------------------------------------- #

# Part 2 input generation (1/2)
cpf = int
nome = str
matr = int
sigaRecord = tuple[cpf, nome, matr]

curso = str
cred = int
matrRecord = tuple[matr,curso,cred]

def randomCurso():
    genero, c0 = choice(curso_geral).split(',')
    c1 = choice(curso_adjetivo)
    c1 = c1.replace('@', genero[0])
    if genero[-1] == 's':
        if '&' in c1 or '$' in c1:
            c1 = c1.replace('&','es').replace('$','is')
        else:
            c1 = c1+'s' if not c1[-1] == '_' else c1[:-1]
    else:
        c1 = c1.replace('&','').replace('$','l')
        c1 = c1.replace('_','') if c1[-1] == '_' else c1
    c2 = choice(curso_especifico)
    return('_'.join([c0.title(),c1.title(),c2.title()]))

# --------------------------------------------------------------------------- #

# Part 2 input generation (2/2)
numClientQueries = 1<<16

nameList = names.words().copy()
cpfList  = sample(range(1000000000,1000000000+len(nameList)), k=len(nameList))
matrList = sample(range(500000,500000+len(nameList)), k=len(nameList))
clientList = choices(cpfList, k=numClientQueries)

sigaDB = {}
matrDB = {}

# 3 Loops to avoid the same element order on the client and both DBs

shuffle(nameList)
with open('siga.txt','w') as fileSiga:
    for idx, name in enumerate(nameList):
        sigaDB |= {cpfList[idx]: [nameList[idx], matrList[idx]]}
        print(f'{cpfList[idx]},{nameList[idx]},{matrList[idx]}', file=fileSiga)
    print(f'T', file=fileSiga)

namesList = list(enumerate(nameList))
shuffle(namesList)
with open('matr.txt','w') as fileMatr:
    for idx, name in namesList:
        matrDB |= {matrList[idx]: [randomCurso(), randint(1,6)]}
        print(f'{matrList[idx],randomCurso(),randint(1,6)}', file=fileMatr)
    print(f'T', file=fileMatr)

shuffle(namesList)
with open(f'client_{numClientQueries}.txt','w') as fileClient:
    for _ in range(20):
        for idx, name in namesList:
            print(f'C,{clientList[idx]}', file=fileClient)
        shuffle(namesList)
    print(f'T', file=fileClient)

shuffle(namesList)
with open('siga.json','w') as jsonSiga, open('matr.json','w') as jsonMatr:
    json.dump(sigaDB, jsonSiga, ensure_ascii=False)
    json.dump(matrDB, jsonMatr, ensure_ascii=False)


# =========================================================================== #