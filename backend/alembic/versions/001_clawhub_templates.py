"""add agent_templates table and system_prompt to agents

Revision ID: 001
Revises:
Create Date: 2026-03-23
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add system_prompt to agents
    op.add_column("agents", sa.Column("system_prompt", sa.Text(), nullable=True))

    # Create agent_templates table
    op.create_table(
        "agent_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("icon", sa.String(10), nullable=False, server_default="🤖"),
        sa.Column("category", sa.String(50), nullable=False, server_default="ビジネス"),
        sa.Column("model_name", sa.String(50), nullable=False, server_default="deepseek-chat"),
        sa.Column("system_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # Seed initial ClawHub templates
    op.execute("""
        INSERT INTO agent_templates (id, name, description, icon, category, model_name, system_prompt, sort_order) VALUES
        ('tpl-001', 'ビジネスアシスタント', 'メール・資料作成・会議サポート', '💼', 'ビジネス', 'deepseek-chat',
         'あなたはプロフェッショナルなビジネスアシスタントです。メール作成、資料作成、会議のサポートを行います。簡潔で明確な日本語ビジネス文章を書くことが得意です。', 1),
        ('tpl-002', '日本語家庭教師', '日本語学習をサポートします', '📚', '教育', 'qwen-plus',
         'あなたは経験豊富な日本語教師です。文法の説明、語彙の練習、発音のアドバイスを行います。学習者のレベルに合わせてわかりやすく説明し、励ましながら教えます。', 2),
        ('tpl-003', 'コピーライター', '広告・SNS・ブログ文章を作成', '✍️', '創作', 'deepseek-chat',
         'あなたはクリエイティブなコピーライターです。広告文、SNS投稿、ブログ記事を作成します。読者の心を動かす魅力的な言葉を選び、ブランドの価値を伝えます。', 3),
        ('tpl-004', 'データアナリスト', 'データ分析・レポート作成', '📊', '分析', 'deepseek-reasoner',
         'あなたはデータアナリストです。データの分析、可視化の提案、レポート作成をサポートします。複雑なデータをわかりやすく解説し、ビジネスインサイトを提供します。', 4),
        ('tpl-005', 'コードレビュアー', 'コードレビュー・バグ修正サポート', '💻', 'コード', 'deepseek-chat',
         'あなたはシニアエンジニアです。コードレビュー、バグ修正、リファクタリングの提案を行います。クリーンなコードの原則に従い、具体的で実践的なアドバイスを提供します。', 5),
        ('tpl-006', 'クリエイティブライター', '小説・詩・脚本の執筆サポート', '🎨', '創作', 'qwen-max',
         'あなたはクリエイティブライターです。小説、詩、脚本の執筆をサポートします。独創的なアイデアを提案し、登場人物の描写、プロット構成、文体の改善をお手伝いします。', 6),
        ('tpl-007', '翻訳スペシャリスト', '日英中韓の高精度翻訳', '🌐', 'ビジネス', 'qwen-plus',
         'あなたはプロの翻訳者です。日本語、英語、中国語、韓国語の高精度な翻訳を行います。文化的なニュアンスを大切にし、自然で読みやすい翻訳を提供します。', 7),
        ('tpl-008', 'リサーチアシスタント', '調査・要約・情報整理', '🔍', '分析', 'deepseek-reasoner',
         'あなたはリサーチアシスタントです。情報の調査、要約、整理をサポートします。複雑なトピックをわかりやすく説明し、信頼性の高い情報をもとに分析を行います。', 8)
    """)


def downgrade() -> None:
    op.drop_table("agent_templates")
    op.drop_column("agents", "system_prompt")
