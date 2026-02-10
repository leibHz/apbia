CREATE TABLE tipos_usuario (
  id INT AUTO_INCREMENT NOT NULL,
  nome VARCHAR(255) NOT NULL UNIQUE,
  PRIMARY KEY (id)
);

CREATE TABLE tipos_ia (
  id INT AUTO_INCREMENT NOT NULL,
  nome VARCHAR(255) NOT NULL UNIQUE,
  PRIMARY KEY (id)
);

CREATE TABLE usuarios (
  id INT AUTO_INCREMENT NOT NULL,
  nome_completo VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  senha_hash VARCHAR(255),
  tipo_usuario_id INT NOT NULL,
  numero_inscricao VARCHAR(255) UNIQUE,
  data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  apelido VARCHAR(255),
  session_token TEXT,
  session_created_at TIMESTAMP NULL,
  last_activity TIMESTAMP NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (tipo_usuario_id) REFERENCES tipos_usuario(id)
);

CREATE TABLE projetos (
  id INT AUTO_INCREMENT NOT NULL,
  nome VARCHAR(255) NOT NULL,
  categoria VARCHAR(255) NOT NULL,
  resumo TEXT,
  palavras_chave TEXT,
  introducao TEXT,
  objetivo_geral TEXT,
  objetivos_especificos JSON,
  metodologia TEXT,
  cronograma JSON,
  resultados_esperados TEXT,
  referencias_bibliograficas TEXT,
  eh_continuacao BOOLEAN DEFAULT FALSE,
  projeto_anterior_titulo VARCHAR(255),
  projeto_anterior_resumo TEXT,
  projeto_anterior_inicio DATE,
  projeto_anterior_termino DATE,
  status VARCHAR(255) DEFAULT 'rascunho',
  ano_edicao INT NOT NULL DEFAULT 2025,
  data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  gerado_por_ia BOOLEAN DEFAULT FALSE,
  prompt_ia_usado TEXT,
  PRIMARY KEY (id)
);

CREATE TABLE chats (
  id INT AUTO_INCREMENT NOT NULL,
  usuario_id INT NOT NULL,
  tipo_ia_id INT NOT NULL,
  titulo VARCHAR(255) NOT NULL,
  data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  notas_orientador TEXT,
  PRIMARY KEY (id),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
  FOREIGN KEY (tipo_ia_id) REFERENCES tipos_ia(id)
);

CREATE TABLE mensagens (
  id BIGINT AUTO_INCREMENT NOT NULL,
  chat_id BIGINT NOT NULL,
  role VARCHAR(255) NOT NULL CHECK (role IN ('user', 'model')),
  conteudo TEXT NOT NULL,
  thinking_process TEXT,
  data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ferramenta_usada VARCHAR(255),
  PRIMARY KEY (id),
  FOREIGN KEY (chat_id) REFERENCES chats(id)
);

CREATE TABLE arquivos_chat (
  id INT AUTO_INCREMENT NOT NULL,
  chat_id INT NOT NULL,
  nome_arquivo VARCHAR(255) NOT NULL,
  url_arquivo VARCHAR(255) NOT NULL,
  tipo_arquivo VARCHAR(255),
  tamanho_bytes BIGINT,
  data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  mensagem_id BIGINT,
  gemini_file_uri TEXT,
  gemini_file_name TEXT,
  gemini_expiration TIMESTAMP NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (chat_id) REFERENCES chats(id),
  FOREIGN KEY (mensagem_id) REFERENCES mensagens(id)
);

CREATE TABLE notas_orientador (
  id BIGINT AUTO_INCREMENT NOT NULL,
  mensagem_id BIGINT NOT NULL,
  orientador_id INT NOT NULL,
  nota TEXT NOT NULL,
  data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (mensagem_id) REFERENCES mensagens(id),
  FOREIGN KEY (orientador_id) REFERENCES usuarios(id)
);

CREATE TABLE observacoes_orientador (
  id BIGINT AUTO_INCREMENT NOT NULL,
  orientador_id BIGINT NOT NULL,
  participante_id BIGINT NOT NULL,
  observacoes TEXT,
  data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (orientador_id) REFERENCES usuarios(id),
  FOREIGN KEY (participante_id) REFERENCES usuarios(id)
);

CREATE TABLE orientadores_projetos (
  orientador_id INT NOT NULL,
  projeto_id INT NOT NULL,
  PRIMARY KEY (orientador_id, projeto_id),
  FOREIGN KEY (orientador_id) REFERENCES usuarios(id)
);

CREATE TABLE participantes_projetos (
  participante_id INT NOT NULL,
  projeto_id INT NOT NULL,
  PRIMARY KEY (participante_id, projeto_id),
  FOREIGN KEY (participante_id) REFERENCES usuarios(id)
);

CREATE TABLE visualizacoes_orientador (
  id BIGINT AUTO_INCREMENT NOT NULL,
  orientador_id INT NOT NULL,
  chat_id INT,
  data_visualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (orientador_id) REFERENCES usuarios(id),
  FOREIGN KEY (chat_id) REFERENCES chats(id)
);

-- execute isso depois (atualização de emergencia)
ALTER TABLE projetos 
ADD COLUMN criador_id INT,
ADD FOREIGN KEY (criador_id) REFERENCES usuarios(id);
-- para o criador original do projeto aparecer, isso é nessesario