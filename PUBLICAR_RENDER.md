# Publicar o PITEP Django no Render

Este passo publica o sistema Django com login, banco PostgreSQL e painel interno.
O Netlify continua servindo bem o painel estático, mas o Django precisa de um
serviço que rode Python no servidor.

## 1. Subir o projeto para o GitHub

O Render publica a partir de um repositório GitHub.

Suba a pasta `sistema-gabinete-django` para um repositório privado ou para o
repositório principal do projeto.

## 2. Criar o serviço no Render

1. Acesse `https://render.com`.
2. Clique em `New`.
3. Escolha `Blueprint`.
4. Conecte o repositório do GitHub.
5. Selecione o arquivo `sistema-gabinete-django/render.yaml`.
6. Confirme a criação.

O `render.yaml` cria:

- serviço web Django;
- banco PostgreSQL;
- variáveis básicas de produção;
- comando de build;
- comando de inicialização com Gunicorn.

## 3. Definir a senha do administrador

No Render, abra o serviço web e entre em `Environment`.

Crie a variável:

```text
ADMIN_PASSWORD
```

Com uma senha forte, por exemplo:

```text
TroquePorUmaSenhaForte@2026
```

O usuário criado será:

```text
thalyne
```

## 4. Conferir o domínio

Depois do deploy, o Render vai gerar um link parecido com:

```text
https://pitep-camila-jara.onrender.com
```

Abra o link e entre com:

```text
Usuário: thalyne
Senha: a senha definida em ADMIN_PASSWORD
```

## 5. Importar a base de dados

Depois que o sistema estiver publicado, use a aba `Shell` do Render para rodar
o importador da planilha publicada como CSV:

```bash
python manage.py import_contacts_google_csv "COLE_AQUI_O_LINK_CSV_DA_BASE_COMPLETA"
```

Se quiser testar antes:

```bash
python manage.py import_contacts_google_csv "COLE_AQUI_O_LINK_CSV_DA_BASE_COMPLETA" --dry-run
```

## 6. Próximas melhorias

- criar permissões por área do gabinete;
- importar emendas no banco Django;
- migrar mapa de calor para o Django;
- criar tela de tarefas e retornos;
- integrar WhatsApp API com consentimento e histórico.
