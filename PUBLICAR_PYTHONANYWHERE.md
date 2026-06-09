# Publicar o sistema Django no PythonAnywhere

Este é o caminho recomendado para colocar o sistema no ar de forma simples para
teste, apresentação e uso inicial.

## 1. Criar conta

1. Acesse `https://www.pythonanywhere.com`.
2. Crie uma conta.
3. Guarde seu nome de usuário. Ele será usado no link:

```text
https://SEU_USUARIO.pythonanywhere.com
```

## 2. Abrir um console Bash

No PythonAnywhere:

1. Clique em `Consoles`.
2. Clique em `Bash`.

## 3. Baixar o projeto do GitHub

No console Bash, rode:

```bash
git clone https://github.com/thalynebarros-netizen/sistema-gabinete-django.git
cd sistema-gabinete-django
```

Se o repositório estiver privado e pedir login, use um token do GitHub ou torne
o repositório público temporariamente apenas se isso for seguro.

## 4. Criar ambiente virtual

Use Python 3.12 ou 3.13, se a conta oferecer essas versões:

```bash
mkvirtualenv --python=/usr/bin/python3.12 pitep-env
```

Se a versão 3.12 não existir na sua conta, tente:

```bash
mkvirtualenv --python=/usr/bin/python3.13 pitep-env
```

Depois instale as dependências:

```bash
pip install -r requirements.txt
```

## 5. Configurar variáveis básicas

Para teste inicial com SQLite, rode:

```bash
export DJANGO_DEBUG=false
export DJANGO_ALLOWED_HOSTS=SEU_USUARIO.pythonanywhere.com,localhost,127.0.0.1
export DJANGO_CSRF_TRUSTED_ORIGINS=https://SEU_USUARIO.pythonanywhere.com
export DJANGO_SECRET_KEY=troque-por-uma-chave-grande-e-segura
export ADMIN_USERNAME=thalyne
export ADMIN_EMAIL=thalyne.barros@ufms.br
export ADMIN_PASSWORD=troque-por-uma-senha-forte
```

Troque `SEU_USUARIO` pelo usuário real do PythonAnywhere.

## 6. Preparar banco, arquivos estáticos e admin

Ainda no console Bash:

```bash
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py bootstrap_admin
```

## 7. Criar Web App

No PythonAnywhere:

1. Clique na aba `Web`.
2. Clique em `Add a new web app`.
3. Escolha seu domínio gratuito: `SEU_USUARIO.pythonanywhere.com`.
4. Escolha `Manual configuration`.
5. Escolha a mesma versão do Python usada no virtualenv.

## 8. Configurar virtualenv na aba Web

Na aba `Web`, procure `Virtualenv`.

Coloque:

```text
/home/SEU_USUARIO/.virtualenvs/pitep-env
```

## 9. Configurar caminho do código

Na aba `Web`, em `Code`, coloque:

```text
Source code: /home/SEU_USUARIO/sistema-gabinete-django
Working directory: /home/SEU_USUARIO/sistema-gabinete-django
```

## 10. Editar arquivo WSGI

Na aba `Web`, clique no link do arquivo WSGI.

Apague o conteúdo e cole o conteúdo do arquivo:

```text
pythonanywhere_wsgi.py
```

Depois troque:

```python
USERNAME = "SEU_USUARIO_PYTHONANYWHERE"
```

pelo seu usuário real.

## 11. Configurar Static Files

Na aba `Web`, em `Static files`, adicione:

```text
URL: /static/
Directory: /home/SEU_USUARIO/sistema-gabinete-django/staticfiles
```

## 12. Recarregar o site

Na aba `Web`, clique em:

```text
Reload
```

Depois abra:

```text
https://SEU_USUARIO.pythonanywhere.com
```

## 13. Login

Use:

```text
Usuário: thalyne
Senha: a senha definida em ADMIN_PASSWORD
```

## Observação importante

Essa configuração inicial usa SQLite. Serve para apresentação e teste.

Para uso oficial do gabinete, o ideal é migrar depois para PostgreSQL, backups,
domínio próprio e política de segurança.
