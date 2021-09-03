#I,ch,um string de descrição,val - insere no servidor a chave ch, associada ao string e ao valor val, escreve na saída padrão o valor de retorno do procedimento (0 ou -1);
#C,ch - consulta o servidor pelo conteúdo associado à chave ch e escreve na saída o string e o valor, separados por uma vírgula, ou apenas -1, caso a chave não seja encontrada;
#T - termina a operação do servidor, envia zero como valor de retorno e termina.

import re

insertCommand = re.compile(r'I,'
    r'(?P<key>\d+),'
    r'(?P<desc>\S+),'
    r'(?P<data>val)'
)


queryCommand = re.compile(r'C,(?P<key>\d+)')


shutdownCommand = re.compile(r'T')

#simpleCommand = Option

print(insertCommand)