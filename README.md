# Renewtri

O Renewtri é uma plataforma digital desenvolvida para auxiliar escolas públicas na gestão da merenda escolar, no controle do desperdício alimentar e no acompanhamento de práticas sustentáveis dentro do ambiente escolar.

O sistema permite registrar a produção alimentar diária, controlar alimentos recebidos, gerenciar merendeiras, acompanhar indicadores em um dashboard e gerar uma previsão simples de preparo com base no histórico registrado pela escola.

## Objetivo

O objetivo do Renewtri é apoiar instituições de ensino no planejamento da merenda escolar, ajudando a reduzir desperdícios, melhorar o controle dos alimentos e facilitar a tomada de decisão com base em dados.

A plataforma foi desenvolvida como um MVP funcional, com foco em organização, facilidade de uso e apresentação para banca avaliadora.

## Tecnologias utilizadas

- Python
- Streamlit
- SQLite
- Pandas
- Plotly

## Funcionalidades

- Login para instituição de ensino
- Login para merendeiras
- Cadastro de instituição
- Cadastro e gerenciamento de merendeiras
- Ativação e desativação de acesso das merendeiras
- Registro de produção alimentar
- Registro de alimentos recebidos
- Controle de desperdício alimentar
- Dashboard com indicadores e gráficos
- Previsão inteligente baseada em histórico
- Área de sustentabilidade
- Banco de dados local com SQLite
- Dados de demonstração para apresentação do MVP

## Estrutura do projeto

```text
Renewtri/
├── app.py
├── auth.py
├── database.py
├── dashboard.py
├── food_production.py
├── food_inventory.py
├── employees.py
├── prediction.py
├── sustainability.py
├── utils.py
├── requirements.txt
└── README.md
```

## Descrição dos arquivos

### app.py

Arquivo principal do sistema. É responsável por iniciar o aplicativo, configurar a página, inicializar o banco de dados, verificar se o usuário está autenticado e controlar a navegação lateral entre as telas.

### auth.py

Responsável pela autenticação. Contém as telas de login e cadastro de instituição, validação de e-mail, login da instituição e login da merendeira.

### database.py

Responsável pelo banco de dados SQLite. Cria automaticamente as tabelas, insere dados de demonstração, salva registros e realiza consultas utilizadas pelas telas do sistema.

### dashboard.py

Responsável pela tela principal do sistema. Exibe cards com indicadores e gráfico de desperdício mensal.

### food_production.py

Responsável pelo cadastro da produção alimentar. Permite registrar data, turno, quantidade de refeições, alimentos utilizados, desperdício em kg e observações.

### food_inventory.py

Responsável pelo cadastro de alimentos recebidos. Permite registrar fornecedor, alimento, quantidade em kg, validade e observações.

### employees.py

Responsável pelo gerenciamento de merendeiras. Permite cadastrar merendeiras, visualizar profissionais cadastradas e ativar ou desativar acessos.

### prediction.py

Responsável pela aba Previsão Inteligente. Utiliza os registros da produção alimentar para gerar recomendações de preparo com base no histórico da escola.

### sustainability.py

Responsável pela aba Sustentabilidade. Apresenta cards, orientações e ações educativas relacionadas à redução do desperdício e educação ambiental.

### utils.py

Contém funções auxiliares usadas no projeto. Inclui formatação de dados, validação de CNPJ, criptografia de senha, geração de código da escola, componentes visuais e CSS personalizado.

## Banco de dados

O sistema utiliza SQLite. O banco de dados é criado automaticamente ao iniciar o aplicativo.

O arquivo do banco fica salvo localmente como:

```text
renewtri.sqlite3
```

As principais tabelas são:

- escolas
- merendeiras
- producao_alimentar
- alimentos_recebidos
- desperdicio
- relatorios
- acessos

## Tipos de usuário

### Instituição de ensino

A instituição pode fazer login com e-mail, CNPJ e senha. Também pode cadastrar merendeiras, ativar e desativar acessos, registrar produção alimentar, registrar alimentos recebidos, acessar o dashboard, consultar a previsão inteligente e visualizar a área de sustentabilidade.

### Merendeira

A merendeira pode fazer login com e-mail, senha e código da escola. Ela pode registrar produção alimentar, consultar informações operacionais e acessar as telas permitidas pelo sistema.

A merendeira não possui acesso ao gerenciamento administrativo de merendeiras.

## Dados de demonstração

O sistema possui dados de demonstração para facilitar a apresentação do MVP.

### Instituição

```text
E-mail: escola@renewtri.demo
CNPJ: 11.222.333/0001-81
Senha: renewtri123
```

### Merendeira

```text
E-mail: robertina@renewtri.demo
Senha: merenda123
Código da escola: aparece ao entrar como instituição
```

## Como executar o projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/PedroCorreiaPPOM/renewtri_.git
```

### 2. Entrar na pasta do projeto

```bash
cd renewtri_
```

### 3. Criar o ambiente virtual

```bash
python -m venv .venv
```

### 4. Ativar o ambiente virtual

No Windows:

```bash
.venv\Scripts\activate
```

No Linux ou macOS:

```bash
source .venv/bin/activate
```

### 5. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 6. Executar o sistema

```bash
python -m streamlit run app.py
```

### 7. Acessar no navegador

```text
http://localhost:8501
```

### Ou acesse o site:

https://renewtri.streamlit.app/

## Requirements

O arquivo `requirements.txt` contém as bibliotecas necessárias para executar o projeto:

```text
streamlit
pandas
plotly
```

## Previsão Inteligente

A Previsão Inteligente do Renewtri não utiliza inteligência artificial avançada.

Ela funciona com uma lógica simples baseada em médias, histórico da produção alimentar, taxa de desperdício, dia da semana, turno e alimentos utilizados anteriormente.

O sistema analisa registros anteriores e sugere uma quantidade recomendada de pratos para os próximos registros, ajudando a escola a planejar melhor a produção da merenda.

## Sustentabilidade

A aba Sustentabilidade apresenta orientações e ações educativas relacionadas a compostagem, reaproveitamento alimentar, redução de desperdício, separação correta do lixo, educação ambiental e conscientização escolar.

## Observações importantes

- O banco de dados é local.
- Cada computador terá seu próprio arquivo SQLite.
- Os dados não são compartilhados automaticamente entre computadores.
- Para uso em equipe, cada integrante deve clonar o repositório e executar o projeto localmente.
- O arquivo `renewtri.sqlite3` não precisa ser enviado para o GitHub.

## Comando principal

Para rodar o sistema, utilize:

```bash
python -m streamlit run app.py
```

## Status do projeto

MVP funcional desenvolvido para apresentação acadêmica e avaliação de proposta tecnológica voltada à gestão da merenda escolar, redução de desperdício alimentar e sustentabilidade.
