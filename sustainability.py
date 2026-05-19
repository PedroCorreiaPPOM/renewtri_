import streamlit as st


def show_sustainability() -> None:
    st.markdown(
        """
        <style>
        .eco-hero {
            padding: 1.4rem;
            border-radius: 14px;
            background: linear-gradient(135deg, #e8f8f1, #eef7ff);
            border: 1px solid #d7ebe4;
            margin-bottom: 1.2rem;
        }

        .eco-hero h1 {
            color: #0b3d3a;
            margin-bottom: .3rem;
        }

        .eco-hero p {
            color: #48606f;
            font-size: 1rem;
            margin: 0;
        }

        .eco-card {
            height: 100%;
            padding: 1rem;
            border-radius: 12px;
            background: white;
            border: 1px solid #dcebe7;
            box-shadow: 0 8px 22px rgba(7, 59, 76, .08);
        }

        .eco-card h3 {
            color: #0b3d3a;
            margin-bottom: .4rem;
            font-size: 1.05rem;
        }

        .eco-card p {
            color: #52697a;
            line-height: 1.45;
            margin: 0;
        }

        .eco-tag {
            display: inline-block;
            padding: .2rem .6rem;
            border-radius: 999px;
            background: #dff6ef;
            color: #08704f;
            font-size: .75rem;
            font-weight: 700;
            margin-bottom: .5rem;
        }

        .tip-box {
            display: flex;
            gap: .75rem;
            padding: .85rem;
            border-radius: 12px;
            background: #ffffff;
            border: 1px solid #dcebe7;
            margin-bottom: .6rem;
        }

        .tip-number {
            min-width: 1.7rem;
            height: 1.7rem;
            border-radius: 50%;
            background: linear-gradient(135deg, #0f9f6e, #0b6fb8);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
        }

        .step-box {
            padding: .9rem 1rem;
            border-left: 5px solid #0f9f6e;
            background: white;
            border-radius: 0 12px 12px 0;
            border-top: 1px solid #dcebe7;
            border-right: 1px solid #dcebe7;
            border-bottom: 1px solid #dcebe7;
            margin-bottom: .7rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="eco-hero">
            <h1>Educação Ambiental</h1>
            <p>
                Acompanhamento de práticas sustentáveis, redução do desperdício alimentar
                e conscientização da comunidade escolar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Kg economizados", "42 kg", "comparação mensal")

    with col2:
        st.metric("Redução de desperdício", "-18%", "melhora estimada")

    with col3:
        st.metric("Aproveitamento alimentar", "84%", "uso eficiente")

    st.markdown("---")

    st.subheader("Plano de ação sustentável")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="eco-card">
                <span class="eco-tag">Compostagem</span>
                <h3>Resíduo vira adubo</h3>
                <p>
                    Separar sobras orgânicas limpas para compostagem ou horta escolar,
                    reduzindo descarte e criando aprendizado prático.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="eco-card">
                <span class="eco-tag">Reaproveitamento</span>
                <h3>Planejamento de cardápio</h3>
                <p>
                    Usar validade, estoque e consumo registrado para priorizar alimentos
                    e evitar perdas antes do preparo.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="eco-card">
                <span class="eco-tag">Conscientização</span>
                <h3>Cultura escolar</h3>
                <p>
                    Transformar dados do Renewtri em campanhas para estudantes,
                    merendeiras e gestão escolar.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    left, right = st.columns([1.1, 0.9])

    with left:
        st.subheader("Dicas sustentáveis")

        dicas = [
            "Compare a produção planejada com a média real de consumo antes de iniciar o preparo.",
            "Registre as sobras diariamente para identificar padrões por turno e por cardápio.",
            "Use o histórico de validade dos alimentos para priorizar os insumos que vencem primeiro.",
            "Incentive os alunos a colocarem no prato apenas o que pretendem consumir.",
            "Divulgue os resultados de economia em murais, reuniões e campanhas educativas.",
        ]

        for index, dica in enumerate(dicas, start=1):
            st.markdown(
                f"""
                <div class="tip-box">
                    <div class="tip-number">{index}</div>
                    <div>{dica}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right:
        st.subheader("Curiosidades ambientais")

        curiosidades = [
            (
                "Impacto invisível",
                "O desperdício de alimentos também representa desperdício de água, energia, transporte e trabalho.",
            ),
            (
                "Compostagem",
                "A compostagem transforma resíduos orgânicos em adubo natural para hortas e jardins.",
            ),
            (
                "Dados como educação",
                "Os indicadores do dashboard podem virar aula prática sobre porcentagem, gráficos e sustentabilidade.",
            ),
        ]

        for titulo, texto in curiosidades:
            st.markdown(
                f"""
                <div class="eco-card" style="margin-bottom: .7rem;">
                    <span class="eco-tag">{titulo}</span>
                    <p>{texto}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    st.subheader("Campanhas escolares")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="eco-card">
                <span class="eco-tag">Campanha 1</span>
                <h3>Semana do Prato Limpo</h3>
                <p>
                    Durante uma semana, cada turma acompanha a redução de sobras
                    e discute escolhas conscientes no momento da merenda.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="eco-card">
                <span class="eco-tag">Campanha 2</span>
                <h3>Desafio Sustentável</h3>
                <p>
                    Turmas propõem ações para reduzir resíduos, melhorar a separação
                    do lixo e divulgar os resultados no mural da escola.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.subheader("Compostagem na prática")

    etapas = [
        ("1. Separar", "Identificar resíduos orgânicos adequados e evitar mistura com plástico, metal ou rejeitos."),
        ("2. Registrar", "Usar o Renewtri para acompanhar a quantidade aproximada de sobras e a evolução semanal."),
        ("3. Destinar", "Encaminhar os resíduos para composteira escolar, horta pedagógica ou parceiro ambiental."),
        ("4. Ensinar", "Transformar o processo em atividade de educação ambiental com participação dos estudantes."),
    ]

    for titulo, texto in etapas:
        st.markdown(
            f"""
            <div class="step-box">
                <strong>{titulo}</strong><br>
                <span>{texto}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )