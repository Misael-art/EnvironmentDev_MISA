# Perfis de Componentes

Os perfis de componentes permitem criar conjuntos pré-definidos de componentes para instalação em massa.

## Comandos Disponíveis

### `profiles create`
Cria um novo perfil de componentes.

```bash
# Criar um perfil com componentes específicos
mecha profiles create meu-perfil --component Git --component Python --component Node.js

# Criar um perfil a partir dos componentes instalados
mecha profiles create meu-perfil --from-installed

# Criar um perfil com descrição
mecha profiles create meu-perfil --component Git --component Python --description "Perfil para desenvolvimento web"
```

### `profiles list`
Lista todos os perfis disponíveis.

```bash
mecha profiles list
```

### `profiles show`
Mostra detalhes de um perfil específico.

```bash
mecha profiles show meu-perfil
```

### `profiles delete`
Exclui um perfil.

```bash
mecha profiles delete meu-perfil
```

### `profiles export`
Exporta um perfil para um arquivo.

```bash
# Exportar em YAML (padrão)
mecha profiles export meu-perfil

# Exportar em JSON
mecha profiles export meu-perfil --format json
```

### `profiles import`
Importa um perfil de um arquivo.

```bash
mecha profiles import meu-perfil.yaml
```

## Usando Perfis

Para instalar todos os componentes de um perfil:

```bash
mecha install-many $(mecha profiles show meu-perfil --json | jq -r '.components[]')
```

Ou crie um alias para facilitar:

```bash
alias instalar-perfil='mecha install-many $(mecha profiles show $1 --json | jq -r ".components[]")'
instalar-perfil meu-perfil
```