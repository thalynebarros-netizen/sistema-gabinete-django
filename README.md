# Sistema do Gabinete em Django

Esta é a nova base para transformar o painel da Camila Jara em um sistema
interno com dados, login real, administração, histórico e integração segura com
WhatsApp.

O painel estático atual continua na raiz do workspace. Esta pasta cresce em
paralelo até substituir os módulos necessários.

## Apps iniciais

- `accounts`: perfis da equipe.
- `dashboard`: visão geral do sistema.
- `contacts`: contatos e histórico.
- `mobilization`: grupos e lideranças de mobilização.
- `emendas`: emendas destinadas.
- `whatsapp_integration`: templates e mensagens WhatsApp.

## Como rodar localmente

Com Python e Django instalados:

```powershell
cd sistema-gabinete-django
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abra `http://127.0.0.1:8000`.

## Banco

Por padrão, o projeto usa SQLite local para desenvolvimento. Quando as
variáveis `POSTGRES_*` forem preenchidas, passa a usar PostgreSQL.

## Próximo passo

Importar a planilha principal para `contacts.Contact`, testar filtros no Django
Admin e ligar o fluxo de login/permissões da equipe.

## Importar contatos da planilha

A importacao inicial usa a aba `Base Completa` da planilha de mapeamento. O
comando usa o `ID` da planilha como chave para atualizar a mesma linha em novas
importacoes e limpa o telefone antes de salvar.

```powershell
cd sistema-gabinete-django
python manage.py import_contacts_xlsx "..\dados\Mapeamento_CamilaJara_ATUALIZADO.xlsx"
```

Para conferir os numeros antes de gravar no banco:

```powershell
python manage.py import_contacts_xlsx "..\dados\Mapeamento_CamilaJara_ATUALIZADO.xlsx" --dry-run
```

As colunas que ainda nao possuem campo proprio ficam guardadas em
`source_payload`, preservando os dados da planilha para migracoes futuras.

Tambem e possivel importar direto de uma aba publicada como CSV no Google
Planilhas:

```powershell
python manage.py import_contacts_google_csv "COLE_AQUI_O_LINK_CSV_DA_BASE_COMPLETA"
```

Antes de gravar no banco, da para simular:

```powershell
python manage.py import_contacts_google_csv "COLE_AQUI_O_LINK_CSV_DA_BASE_COMPLETA" --dry-run
```

## Vincular dados do CRM Luva

Depois de importar a Base Completa, use o CSV exportado do Luva para marcar os
contatos que vieram do CRM, guardar status/fonte/responsavel originais e criar
os leads do Luva que ainda nao existirem no banco.

```powershell
python manage.py enrich_contacts_luva_csv "C:\Users\raulg\Downloads\segmento_1_todos-os-leads_camila-jara_LEADS-COMPLETO_export_2026_04_23_17_49_32.csv"
```

Para conferir sem gravar:

```powershell
python manage.py enrich_contacts_luva_csv "C:\Users\raulg\Downloads\segmento_1_todos-os-leads_camila-jara_LEADS-COMPLETO_export_2026_04_23_17_49_32.csv" --dry-run
```
