<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import {
  completeLessonApi,
  fetchDashboard,
  guestLogin,
  runPipeline,
  startLesson,
  submitLessonPhase,
  tutorChat,
} from "./api";

const apiBase = ref("http://localhost:8000");
const loading = ref(false);
const ttsLoading = ref(false);
const sessionModalOpen = ref(false);
const onboardingChoiceModalOpen = ref(false);
const lessonPlayerOpen = ref(false);
const activeLessonIndex = ref(0);
const activePhaseIndex = ref(0);
const lessonNetworkBusy = ref(false);
const error = ref("");
const ttsStatus = ref("");
const result = ref(null);
const dashboardData = ref(null);
const step = ref(0);
const currentPath = ref(window.location.pathname || "/");
const displayName = ref("Learner");
const userName = ref("");
const lessonsPerWeek = ref(2);
const aiFeedbackLoading = ref(false);
const aiFeedback = ref("");
const tutorConversation = ref([]);
const tutorMemory = ref({});
const reviewSessionOpen = ref(false);
const activeReviewIndex = ref(0);
const pipelineLoadingStep = ref(0);
const sttConfidence = ref(0);
const notificationsPermission = ref(
  typeof Notification !== "undefined" ? Notification.permission : "denied",
);
const phaseStartTime = ref(Date.now());
const guidedHintsVisible = ref([]);
const currentStreak = ref(0);
const guidedCheckResults = ref([]);
const guidedCheckLoading = ref([]);

const speakLanguages = [
  { code: "en", label: "English", emoji: "🇬🇧" },
  { code: "nl", label: "Dutch", emoji: "🇳🇱" },
  { code: "es", label: "Spanish", emoji: "🇪🇸" },
  { code: "fr", label: "French", emoji: "🇫🇷" },
  { code: "de", label: "German", emoji: "🇩🇪" },
  { code: "it", label: "Italian", emoji: "🇮🇹" },
  { code: "ja", label: "Japanese", emoji: "🇯🇵" },
];

const learnLanguages = [
  { code: "fr", label: "French", emoji: "🇫🇷" },
  { code: "nl", label: "Dutch", emoji: "🇳🇱" },
  { code: "es", label: "Spanish", emoji: "🇪🇸" },
  { code: "de", label: "German", emoji: "🇩🇪" },
  { code: "en", label: "English", emoji: "🇬🇧" },
  { code: "hi", label: "Hindi", emoji: "🇮🇳" },
  { code: "ja", label: "Japanese", emoji: "🇯🇵" },
];
const landingFeatures = [
  {
    title: "Adaptive AI Assessment",
    description:
      "Discover your real language level with personalized prompts and feedback that evolve with every response.",
  },
  {
    title: "Deep Learning Workflows",
    description:
      "Weekly plans and focused sessions keep your progress structured, measurable, and practical.",
  },
  {
    title: "Speaking-First Practice",
    description:
      "Train for real conversations with confidence, clear feedback, and progressive challenge levels.",
  },
];
const landingJourney = [
  {
    title: "Take the assessment",
    description:
      "We analyze your communication style and fluency to build a tailored learning path.",
    visual: "⌨️",
  },
  {
    title: "Get your weekly plan",
    description:
      "Receive practical daily lessons and progress milestones aligned with your goals.",
    visual: "🗓️",
  },
  {
    title: "Practice with your AI tutor",
    description:
      "Short, focused sessions reinforce weak areas while preserving your strengths.",
    visual: "🎯",
  },
];

const selectedSpeakCode = ref("en");
const selectedLearnCode = ref("fr");
const uiTextBySpeak = {
  en: {
    alreadySpeak: "I ALREADY SPEAK...",
    wantLearn: "I WANT TO LEARN...",
    continueJourney: "Continue Journey ->",
    helperText: "You can change these settings anytime from your profile.",
    onboardingTitle: "How would you like to begin?",
    onboardingDesc:
      "Do you want to start from level zero, or do an assessment so we can detect your weak points and build a personalized plan?",
    startZero: "Start from zero",
    doAssessment: "Do assessment and personalize my plan",
    cancel: "Cancel",
    assessmentStep: "ASSESSMENT: STEP",
    of: "OF",
    complete: "Complete",
    assessmentTip: "TIP: questions are shown in",
    answerIn: "answer in",
    welcomeBack: "Welcome back,",
    readyDaily: "Ready for your daily linguistic exercise?",
    plan12w: "Your 3-Month Plan (12 weeks)",
    viewCalendar: "View Calendar",
    locked: "Locked",
    completed: "Completed",
    start: "Start",
    needSupportLibrary: "Need support? Check the Library tab for vocabulary and examples before you answer.",
    speakingExercise: "Speaking exercise",
    speakingFirst: "Speaking-first mode: use the microphone first. Typing is only a backup.",
    generateFollowUp: "Generate follow-up speaking question",
    followUpFeedback: "Follow-up feedback",
    focusAreas: "Focus areas from your assessment:",
    previousPhase: "Previous phase",
    continueNextPhase: "Continue to next phase",
    finishLesson: "Finish lesson",
    error: "Error",
    warmupValidation: "Answer at least 2 warm-up questions with a full sentence.",
    inputVocabValidation: "Mark at least {n} words as learned before continuing.",
    inputCheckValidation: "Fill in the short input check before continuing.",
    guidedValidation: "Complete all guided practice exercises.",
    outputMinValidation: "Give a longer answer (at least 20 characters) in the output phase.",
    outputNeedFollowQuestion: "Generate the follow-up speaking question first, then answer it.",
    outputNeedFollowAnswer: "Answer the follow-up speaking question before continuing.",
    feedbackValidation: "Write a short reflection before finishing the lesson.",
    followupNeedBase: "Give your first speaking answer before generating the follow-up question.",
    navHowItWorks: "How it works",
    navFeatures: "Features",
    navPricing: "Pricing",
    navSignIn: "Sign In",
    navGetStarted: "Get Started",
    heroGetStartedNow: "Get Started Now",
    appTitle: "Vlot",
    apiBaseUrl: "API Base URL",
    userId: "User ID",
    sessionId: "Session ID",
    loadingPlan: "AI is creating your plan...",
    startOver: "Start over",
    skillInsightsTitle: "Skill Insights",
    coachTipTitle: "COACH'S TIP",
    speakingLoading: "Speaking...",
    readAloud: "Read aloud",
    recentAchievement: "Recent Achievement",
    learningMetrics: "Learning Metrics",
    reviewDueTodayTitle: "Review Due Today",
    noDueReviews: "No due reviews. Great consistency.",
    planTabTitle: "Your learning plan",
    currentLevel: "Current level",
    targetLevel: "Target level",
    duration: "Duration",
    lessonsDone: "Lessons done",
    level: "Level",
    progressTabTitle: "Your progress",
    skillBreakdown: "Skill breakdown",
    lessonHistory: "Lesson history",
    settingsTitle: "Settings",
    settingsLanguages: "Languages",
    settingsISpeak: "I speak",
    settingsImLearning: "I'm learning",
    settingsTts: "Text-to-speech",
    settingsEnableTts: "Enable TTS",
    settingsSpeakingSpeed: "Speaking speed",
    settingsVoice: "Voice",
    testVoice: "Test voice",
    settingsSession: "Session",
    reset: "Reset",
    sidebarCurriculum: "Curriculum",
    sidebarLibrary: "Library",
    sidebarInsights: "Insights",
    sidebarSettings: "Settings",
    lessonSettingsTitle: "Lesson settings",
    readLessonAloud: "Read lesson text aloud",
    backToDashboard: "Back to dashboard",
    currentProgress: "CURRENT PROGRESS",
    sessionCompleteTitle: "Session Complete",
    sessionCompleteBody: "Excellent progress! You're building stronger fluency and confidence with every lesson.",
    levelProgress: "Level 4 Progress",
    xpEarnedLabel: "XP EARNED",
    accuracyLabel: "ACCURACY",
    nextLesson: "Next lesson",
    reviewMistakes: "Review Mistakes",
    privacyPolicy: "Privacy Policy",
    termsOfService: "Terms of Service",
    contactUs: "Contact Us",
    seeHowItWorks: "See how it works",
    heroProgressTitle: "You're making progress",
    heroProgressSubtitle: "Ready for your next speaking lesson.",
    eleganceTitle: "Elegance in Education",
    quietPersistence: "Quiet Persistence",
    nextMilestone: "Next milestone in 158 XP",
    quietRewards: "Quiet Rewards",
    scheduleDemo: "Schedule a Demo",
    risingLearner: "Rising Learner",
    level4: "Level 4",
    streakBadge: "4-day streak - keep it up!",
    totalXp: "Total XP",
    avgAccuracy: "Avg accuracy",
    reviewsDue: "Reviews due",
    reviewDueTodaySection: "Review due today",
    readLessonWordsAloud: "Read lesson text and words aloud",
    resetSessionDesc: "Reset your session and take a new assessment",
    yourLessons: "Your lessons",
    wordBank: "Word bank",
    yourProgress: "Your progress",
    skillScores: "Skill scores",
    learning: "Learning",
    feedback: "Feedback",
    starterWordsHint: "Starter words — use these to answer the questions below",
    practicedToday: "What you practiced today",
    sessionStats: "Session stats",
    xpEarnedInline: "XP earned",
    accuracyInline: "Accuracy",
    thingsToReview: "Things to review",
    insteadOf: "Instead of:",
    tryLabel: "Try:",
    nextLessonFocus: "What will you focus on next lesson?",
    twitter: "Twitter",
    linkedIn: "LinkedIn",
    heroHeadingPrefix: "The Mature Way to",
    heroHeadingHighlight: "Master",
    heroHeadingSuffix: "a New Language",
    journeyTitlePrefix: "The Journey to",
    journeyTitleHighlight: "Fluency",
    finalCtaPrefix: "Start Your Journey to",
    finalCtaHighlight: "Fluency",
    finalCtaSuffix: "Today",
    languageFocusTagline: "begins with focus.",
    streakDays: "42 Days",
    youLabel: "YOU",
  },
  nl: {
    alreadySpeak: "IK SPREEK AL...",
    wantLearn: "IK WIL LEREN...",
    continueJourney: "Ga verder ->",
    helperText: "Je kunt deze instellingen altijd aanpassen in je profiel.",
    onboardingTitle: "Hoe wil je beginnen?",
    onboardingDesc:
      "Wil je vanaf nul starten, of een assessment doen zodat we je zwakke punten vinden en een persoonlijk plan maken?",
    startZero: "Start vanaf nul",
    doAssessment: "Doe assessment en personaliseer mijn plan",
    cancel: "Annuleren",
    assessmentStep: "ASSESSMENT: STAP",
    of: "VAN",
    complete: "Voltooid",
    assessmentTip: "TIP: vragen worden getoond in",
    answerIn: "antwoord in",
    welcomeBack: "Welkom terug,",
    readyDaily: "Klaar voor je dagelijkse taaloefening?",
    plan12w: "Jouw 3-maandenplan (12 weken)",
    viewCalendar: "Bekijk kalender",
    locked: "Vergrendeld",
    completed: "Voltooid",
    start: "Start",
    needSupportLibrary: "Hulp nodig? Kijk in de Library voor woordenschat en voorbeelden voordat je antwoordt.",
    speakingExercise: "Spreekoefening",
    speakingFirst: "Spreken eerst: gebruik eerst de microfoon. Typen is alleen een back-up.",
    generateFollowUp: "Genereer vervolgvraag voor spreken",
    followUpFeedback: "Feedback op vervolgvraag",
    focusAreas: "Focuspunten uit je assessment:",
    previousPhase: "Vorige fase",
    continueNextPhase: "Ga naar volgende fase",
    finishLesson: "Les afronden",
    error: "Fout",
    warmupValidation: "Beantwoord minimaal 2 warm-up vragen met een volledige zin.",
    inputVocabValidation: "Markeer minimaal {n} woorden als geleerd voordat je doorgaat.",
    inputCheckValidation: "Vul de korte input-check in voor je doorgaat.",
    guidedValidation: "Vul alle guided practice oefeningen in.",
    outputMinValidation: "Geef een langer antwoord (minimaal 20 tekens) in de output-fase.",
    outputNeedFollowQuestion: "Genereer eerst de vervolgvraag en beantwoord die daarna.",
    outputNeedFollowAnswer: "Beantwoord de vervolgvraag voordat je doorgaat.",
    feedbackValidation: "Schrijf een korte reflectie voordat je de les afrondt.",
    followupNeedBase: "Geef eerst je eerste spreekantwoord voordat je een vervolgvraag maakt.",
    navHowItWorks: "Hoe het werkt",
    navFeatures: "Features",
    navPricing: "Prijzen",
    navSignIn: "Inloggen",
    navGetStarted: "Start",
    heroGetStartedNow: "Start nu",
    appTitle: "Vlot",
    apiBaseUrl: "API Basis-URL",
    userId: "Gebruikers-ID",
    sessionId: "Sessie-ID",
    loadingPlan: "AI maakt je plan...",
    startOver: "Opnieuw beginnen",
    skillInsightsTitle: "Skill-inzichten",
    coachTipTitle: "TIP VAN DE COACH",
    speakingLoading: "Spreekt...",
    readAloud: "Hardop lezen",
    recentAchievement: "Recente prestatie",
    learningMetrics: "Leerstatistieken",
    reviewDueTodayTitle: "Vandaag te herhalen",
    noDueReviews: "Geen herhaling vandaag. Sterke consistentie.",
    planTabTitle: "Jouw leerplan",
    currentLevel: "Huidig niveau",
    targetLevel: "Doelniveau",
    duration: "Duur",
    lessonsDone: "Lessen gedaan",
    level: "Niveau",
    progressTabTitle: "Jouw voortgang",
    skillBreakdown: "Vaardighedenoverzicht",
    lessonHistory: "Lesgeschiedenis",
    settingsTitle: "Instellingen",
    settingsLanguages: "Talen",
    settingsISpeak: "Ik spreek",
    settingsImLearning: "Ik leer",
    settingsTts: "Tekst-naar-spraak",
    settingsEnableTts: "TTS aanzetten",
    settingsSpeakingSpeed: "Spreeksnelheid",
    settingsVoice: "Stem",
    testVoice: "Test stem",
    settingsSession: "Sessie",
    reset: "Reset",
    sidebarCurriculum: "Curriculum",
    sidebarLibrary: "Library",
    sidebarInsights: "Inzichten",
    sidebarSettings: "Instellingen",
    lessonSettingsTitle: "Lesinstellingen",
    readLessonAloud: "Lees les hardop",
    backToDashboard: "Terug naar dashboard",
    currentProgress: "HUIDIGE VOORTGANG",
    sessionCompleteTitle: "Sessie voltooid",
    sessionCompleteBody: "Uitstekende voortgang! Je bouwt met elke les meer vloeiendheid en zelfvertrouwen op.",
    levelProgress: "Niveau 4 voortgang",
    xpEarnedLabel: "XP VERDIEND",
    accuracyLabel: "NAUWKEURIGHEID",
    nextLesson: "Volgende les",
    reviewMistakes: "Fouten herhalen",
    privacyPolicy: "Privacybeleid",
    termsOfService: "Servicevoorwaarden",
    contactUs: "Contact",
    seeHowItWorks: "Bekijk hoe het werkt",
    heroProgressTitle: "Je boekt vooruitgang",
    heroProgressSubtitle: "Klaar voor je volgende spreekles.",
    eleganceTitle: "Elegantie in Educatie",
    quietPersistence: "Stille volharding",
    nextMilestone: "Volgende mijlpaal bij 158 XP",
    quietRewards: "Stille beloningen",
    scheduleDemo: "Plan een demo",
    risingLearner: "Groeiende leerling",
    level4: "Niveau 4",
    streakBadge: "4-daagse streak - ga zo door!",
    totalXp: "Totale XP",
    avgAccuracy: "Gem. nauwkeurigheid",
    reviewsDue: "Herhalingen open",
    reviewDueTodaySection: "Vandaag te herhalen",
    readLessonWordsAloud: "Lees lestekst en woorden hardop",
    resetSessionDesc: "Reset je sessie en doe een nieuwe assessment",
    yourLessons: "Jouw lessen",
    wordBank: "Woordenbank",
    yourProgress: "Jouw voortgang",
    skillScores: "Vaardigheidsscores",
    learning: "Leren",
    feedback: "Feedback",
    starterWordsHint: "Startwoorden — gebruik deze om de vragen hieronder te beantwoorden",
    practicedToday: "Wat je vandaag hebt geoefend",
    sessionStats: "Sessiestatistieken",
    xpEarnedInline: "XP verdiend",
    accuracyInline: "Nauwkeurigheid",
    thingsToReview: "Punten om te herhalen",
    insteadOf: "In plaats van:",
    tryLabel: "Probeer:",
    nextLessonFocus: "Waar wil je in de volgende les op focussen?",
    twitter: "Twitter",
    linkedIn: "LinkedIn",
    heroHeadingPrefix: "De volwassen manier om",
    heroHeadingHighlight: "te beheersen",
    heroHeadingSuffix: "een nieuwe taal",
    journeyTitlePrefix: "De reis naar",
    journeyTitleHighlight: "vloeiendheid",
    finalCtaPrefix: "Start jouw reis naar",
    finalCtaHighlight: "vloeiendheid",
    finalCtaSuffix: "vandaag",
    languageFocusTagline: "begint met focus.",
    streakDays: "42 dagen",
    youLabel: "JIJ",
  },
  es: {
    alreadySpeak: "YA HABLO...",
    wantLearn: "QUIERO APRENDER...",
    continueJourney: "Continuar ->",
    helperText: "Puedes cambiar estos ajustes en cualquier momento desde tu perfil.",
    onboardingTitle: "¿Cómo quieres empezar?",
    onboardingDesc:
      "¿Quieres empezar desde cero o hacer una evaluación para detectar puntos débiles y crear un plan personalizado?",
    startZero: "Empezar desde cero",
    doAssessment: "Hacer evaluación y personalizar mi plan",
    cancel: "Cancelar",
    assessmentStep: "EVALUACIÓN: PASO",
    of: "DE",
    complete: "Completado",
    assessmentTip: "CONSEJO: las preguntas se muestran en",
    answerIn: "responde en",
    welcomeBack: "Bienvenido de nuevo,",
    readyDaily: "¿Listo para tu ejercicio lingüístico diario?",
    plan12w: "Tu plan de 3 meses (12 semanas)",
    viewCalendar: "Ver calendario",
    locked: "Bloqueado",
    completed: "Completado",
    start: "Empezar",
    needSupportLibrary: "¿Necesitas ayuda? Revisa la pestaña Library para vocabulario y ejemplos antes de responder.",
    speakingExercise: "Ejercicio de conversación",
    speakingFirst: "Modo hablar primero: usa primero el micrófono. Escribir es solo respaldo.",
    generateFollowUp: "Generar pregunta de seguimiento oral",
    followUpFeedback: "Feedback de seguimiento",
    focusAreas: "Áreas de enfoque de tu evaluación:",
    previousPhase: "Fase anterior",
    continueNextPhase: "Continuar a la siguiente fase",
    finishLesson: "Finalizar lección",
    error: "Error",
    warmupValidation: "Responde al menos 2 preguntas de warm-up con una oración completa.",
    inputVocabValidation: "Marca al menos {n} palabras como aprendidas antes de continuar.",
    inputCheckValidation: "Completa la breve comprobación de input antes de continuar.",
    guidedValidation: "Completa todos los ejercicios de práctica guiada.",
    outputMinValidation: "Da una respuesta más larga (al menos 20 caracteres) en la fase de output.",
    outputNeedFollowQuestion: "Genera primero la pregunta de seguimiento y luego respóndela.",
    outputNeedFollowAnswer: "Responde la pregunta de seguimiento antes de continuar.",
    feedbackValidation: "Escribe una breve reflexión antes de terminar la lección.",
    followupNeedBase: "Da primero tu respuesta oral inicial antes de generar la pregunta de seguimiento.",
    navHowItWorks: "Cómo funciona",
    navFeatures: "Funciones",
    navPricing: "Precios",
    navSignIn: "Iniciar sesión",
    navGetStarted: "Comenzar",
    heroGetStartedNow: "Comenzar ahora",
    appTitle: "Vlot",
    apiBaseUrl: "URL base de API",
    userId: "ID de usuario",
    sessionId: "ID de sesión",
    loadingPlan: "La IA está creando tu plan...",
    startOver: "Empezar de nuevo",
    skillInsightsTitle: "Insights de habilidades",
    coachTipTitle: "TIP DEL COACH",
    speakingLoading: "Hablando...",
    readAloud: "Leer en voz alta",
    recentAchievement: "Logro reciente",
    learningMetrics: "Métricas de aprendizaje",
    reviewDueTodayTitle: "Repaso para hoy",
    noDueReviews: "No hay repasos pendientes hoy. Gran constancia.",
    planTabTitle: "Tu plan de aprendizaje",
    currentLevel: "Nivel actual",
    targetLevel: "Nivel objetivo",
    duration: "Duración",
    lessonsDone: "Lecciones completadas",
    progressTabTitle: "Tu progreso",
    skillBreakdown: "Desglose de habilidades",
    lessonHistory: "Historial de lecciones",
    settingsTitle: "Configuración",
    settingsLanguages: "Idiomas",
    settingsISpeak: "Hablo",
    settingsImLearning: "Estoy aprendiendo",
    settingsTts: "Texto a voz",
    settingsEnableTts: "Activar TTS",
    settingsSpeakingSpeed: "Velocidad de voz",
    settingsVoice: "Voz",
    testVoice: "Probar voz",
    settingsSession: "Sesión",
    reset: "Reiniciar",
    sidebarCurriculum: "Currículum",
    sidebarLibrary: "Library",
    sidebarInsights: "Insights",
    sidebarSettings: "Configuración",
    lessonSettingsTitle: "Ajustes de lección",
    readLessonAloud: "Leer texto de la lección en voz alta",
    backToDashboard: "Volver al dashboard",
    currentProgress: "PROGRESO ACTUAL",
    sessionCompleteTitle: "Sesión completada",
    sessionCompleteBody: "¡Excelente progreso! Estás mejorando fluidez y confianza en cada lección.",
    levelProgress: "Progreso nivel 4",
    xpEarnedLabel: "XP GANADA",
    accuracyLabel: "PRECISIÓN",
    nextLesson: "Siguiente lección",
    reviewMistakes: "Revisar errores",
    privacyPolicy: "Política de privacidad",
    termsOfService: "Términos de servicio",
    contactUs: "Contacto",
    seeHowItWorks: "Ver cómo funciona",
    heroProgressTitle: "Estás progresando",
    heroProgressSubtitle: "Listo para tu próxima lección de speaking.",
    eleganceTitle: "Elegancia en la educación",
    quietPersistence: "Persistencia silenciosa",
    nextMilestone: "Próximo hito en 158 XP",
    quietRewards: "Recompensas silenciosas",
    scheduleDemo: "Programar una demo",
    risingLearner: "Aprendiz en crecimiento",
    level4: "Nivel 4",
    streakBadge: "racha de 4 días - ¡sigue así!",
    totalXp: "XP total",
    avgAccuracy: "Precisión media",
    reviewsDue: "Repasos pendientes",
    reviewDueTodaySection: "Repaso para hoy",
    readLessonWordsAloud: "Leer en voz alta texto y palabras de la lección",
    resetSessionDesc: "Reinicia tu sesión y haz una nueva evaluación",
    yourLessons: "Tus lecciones",
    wordBank: "Banco de palabras",
    yourProgress: "Tu progreso",
    skillScores: "Puntuación de habilidades",
    learning: "Aprendizaje",
    feedback: "Feedback",
    starterWordsHint: "Palabras iniciales: úsalas para responder las preguntas de abajo",
    practicedToday: "Lo que practicaste hoy",
    sessionStats: "Estadísticas de sesión",
    xpEarnedInline: "XP ganada",
    accuracyInline: "Precisión",
    thingsToReview: "Puntos para repasar",
    insteadOf: "En lugar de:",
    tryLabel: "Prueba:",
    nextLessonFocus: "¿En qué te enfocarás en la próxima lección?",
    level: "Nivel",
    twitter: "Twitter",
    linkedIn: "LinkedIn",
    heroHeadingPrefix: "La forma madura de",
    heroHeadingHighlight: "dominar",
    heroHeadingSuffix: "un nuevo idioma",
    journeyTitlePrefix: "El camino hacia",
    journeyTitleHighlight: "la fluidez",
    finalCtaPrefix: "Comienza tu camino hacia",
    finalCtaHighlight: "la fluidez",
    finalCtaSuffix: "hoy",
    languageFocusTagline: "empieza con enfoque.",
    streakDays: "42 días",
    youLabel: "TÚ",
  },
  fr: {
    alreadySpeak: "JE PARLE DÉJÀ...",
    wantLearn: "JE VEUX APPRENDRE...",
    continueJourney: "Continuer ->",
    helperText: "Vous pouvez modifier ces paramètres à tout moment depuis votre profil.",
    onboardingTitle: "Comment souhaitez-vous commencer ?",
    onboardingDesc:
      "Voulez-vous commencer de zéro, ou faire une évaluation pour détecter vos points faibles et créer un plan personnalisé ?",
    startZero: "Commencer de zéro",
    doAssessment: "Faire l'évaluation et personnaliser mon plan",
    cancel: "Annuler",
    assessmentStep: "ÉVALUATION : ÉTAPE",
    of: "SUR",
    complete: "Terminé",
    assessmentTip: "ASTUCE : les questions sont affichées en",
    answerIn: "répondez en",
    welcomeBack: "Bon retour,",
    readyDaily: "Prêt pour votre exercice linguistique quotidien ?",
    plan12w: "Votre plan de 3 mois (12 semaines)",
    viewCalendar: "Voir le calendrier",
    locked: "Verrouillé",
    completed: "Terminé",
    start: "Commencer",
    needSupportLibrary: "Besoin d'aide ? Consultez l'onglet Library pour le vocabulaire et les exemples avant de répondre.",
    speakingExercise: "Exercice oral",
    speakingFirst: "Mode priorité à l'oral : utilisez d'abord le micro. La saisie est un secours.",
    generateFollowUp: "Générer une question orale de suivi",
    followUpFeedback: "Retour de suivi",
    focusAreas: "Axes de travail issus de votre évaluation :",
    previousPhase: "Phase précédente",
    continueNextPhase: "Passer à la phase suivante",
    finishLesson: "Terminer la leçon",
    error: "Erreur",
    warmupValidation: "Répondez à au moins 2 questions d'échauffement avec une phrase complète.",
    inputVocabValidation: "Cochez au moins {n} mots comme appris avant de continuer.",
    inputCheckValidation: "Remplissez la vérification courte de la phase input avant de continuer.",
    guidedValidation: "Complétez tous les exercices de pratique guidée.",
    outputMinValidation: "Donnez une réponse plus longue (au moins 20 caractères) en phase output.",
    outputNeedFollowQuestion: "Générez d'abord la question de suivi puis répondez-y.",
    outputNeedFollowAnswer: "Répondez à la question de suivi avant de continuer.",
    feedbackValidation: "Écrivez une courte réflexion avant de terminer la leçon.",
    followupNeedBase: "Donnez d'abord votre première réponse orale avant de générer la question de suivi.",
    navHowItWorks: "Comment ça marche",
    navFeatures: "Fonctionnalités",
    navPricing: "Tarifs",
    navSignIn: "Se connecter",
    navGetStarted: "Commencer",
    heroGetStartedNow: "Commencer maintenant",
    appTitle: "Vlot",
    apiBaseUrl: "URL de base API",
    userId: "ID utilisateur",
    sessionId: "ID session",
    loadingPlan: "L'IA crée votre plan...",
    startOver: "Recommencer",
    skillInsightsTitle: "Insights de compétences",
    coachTipTitle: "CONSEIL DU COACH",
    speakingLoading: "Lecture...",
    readAloud: "Lire à voix haute",
    recentAchievement: "Succès récent",
    learningMetrics: "Indicateurs d'apprentissage",
    reviewDueTodayTitle: "Révisions du jour",
    noDueReviews: "Aucune révision due aujourd'hui. Super régularité.",
    planTabTitle: "Votre plan d'apprentissage",
    currentLevel: "Niveau actuel",
    targetLevel: "Niveau cible",
    duration: "Durée",
    lessonsDone: "Leçons terminées",
    progressTabTitle: "Votre progression",
    skillBreakdown: "Répartition des compétences",
    lessonHistory: "Historique des leçons",
    settingsTitle: "Paramètres",
    settingsLanguages: "Langues",
    settingsISpeak: "Je parle",
    settingsImLearning: "J'apprends",
    settingsTts: "Synthèse vocale",
    settingsEnableTts: "Activer TTS",
    settingsSpeakingSpeed: "Vitesse de parole",
    settingsVoice: "Voix",
    testVoice: "Tester la voix",
    settingsSession: "Session",
    reset: "Réinitialiser",
    sidebarCurriculum: "Curriculum",
    sidebarLibrary: "Library",
    sidebarInsights: "Insights",
    sidebarSettings: "Paramètres",
    lessonSettingsTitle: "Paramètres de leçon",
    readLessonAloud: "Lire le texte de la leçon à voix haute",
    backToDashboard: "Retour au dashboard",
    currentProgress: "PROGRESSION ACTUELLE",
    sessionCompleteTitle: "Session terminée",
    sessionCompleteBody: "Excellent progrès ! Vous développez fluidité et confiance à chaque leçon.",
    levelProgress: "Progression niveau 4",
    xpEarnedLabel: "XP GAGNÉE",
    accuracyLabel: "PRÉCISION",
    nextLesson: "Leçon suivante",
    reviewMistakes: "Revoir les erreurs",
    privacyPolicy: "Politique de confidentialité",
    termsOfService: "Conditions d'utilisation",
    contactUs: "Contact",
    seeHowItWorks: "Voir comment ça marche",
    heroProgressTitle: "Vous progressez",
    heroProgressSubtitle: "Prêt pour votre prochaine leçon d'oral.",
    eleganceTitle: "L'élégance de l'éducation",
    quietPersistence: "Persévérance discrète",
    nextMilestone: "Prochain palier à 158 XP",
    quietRewards: "Récompenses discrètes",
    scheduleDemo: "Planifier une démo",
    risingLearner: "Apprenant en progression",
    level4: "Niveau 4",
    streakBadge: "série de 4 jours - continuez !",
    totalXp: "XP totale",
    avgAccuracy: "Précision moyenne",
    reviewsDue: "Révisions à faire",
    reviewDueTodaySection: "Révisions du jour",
    readLessonWordsAloud: "Lire à voix haute le texte et les mots de la leçon",
    resetSessionDesc: "Réinitialisez votre session et refaites une évaluation",
    yourLessons: "Vos leçons",
    wordBank: "Banque de mots",
    yourProgress: "Votre progression",
    skillScores: "Scores de compétences",
    learning: "Apprentissage",
    feedback: "Feedback",
    starterWordsHint: "Mots de départ — utilisez-les pour répondre aux questions ci-dessous",
    practicedToday: "Ce que vous avez pratiqué aujourd'hui",
    sessionStats: "Statistiques de session",
    xpEarnedInline: "XP gagnée",
    accuracyInline: "Précision",
    thingsToReview: "Points à revoir",
    insteadOf: "Au lieu de :",
    tryLabel: "Essayez :",
    nextLessonFocus: "Sur quoi allez-vous vous concentrer à la prochaine leçon ?",
    level: "Niveau",
    twitter: "Twitter",
    linkedIn: "LinkedIn",
    heroHeadingPrefix: "La manière adulte de",
    heroHeadingHighlight: "maîtriser",
    heroHeadingSuffix: "une nouvelle langue",
    journeyTitlePrefix: "Le chemin vers",
    journeyTitleHighlight: "la fluidité",
    finalCtaPrefix: "Commencez votre chemin vers",
    finalCtaHighlight: "la fluidité",
    finalCtaSuffix: "aujourd'hui",
    languageFocusTagline: "commence par la concentration.",
    streakDays: "42 jours",
    youLabel: "VOUS",
  },
  de: {
    alreadySpeak: "ICH SPRECHE BEREITS...",
    wantLearn: "ICH MÖCHTE LERNEN...",
    continueJourney: "Weiter ->",
    helperText: "Du kannst diese Einstellungen jederzeit in deinem Profil ändern.",
    onboardingTitle: "Wie möchtest du beginnen?",
    onboardingDesc:
      "Möchtest du bei null starten oder ein Assessment machen, damit wir Schwächen erkennen und einen persönlichen Plan erstellen?",
    startZero: "Bei null starten",
    doAssessment: "Assessment machen und Plan personalisieren",
    cancel: "Abbrechen",
    assessmentStep: "ASSESSMENT: SCHRITT",
    of: "VON",
    complete: "Abgeschlossen",
    assessmentTip: "TIPP: Fragen werden in",
    answerIn: "beantworte in",
    welcomeBack: "Willkommen zurück,",
    readyDaily: "Bereit für deine tägliche Sprachübung?",
    plan12w: "Dein 3-Monats-Plan (12 Wochen)",
    viewCalendar: "Kalender anzeigen",
    locked: "Gesperrt",
    completed: "Abgeschlossen",
    start: "Start",
    needSupportLibrary: "Brauchst du Hilfe? Schau im Library-Tab nach Vokabeln und Beispielen, bevor du antwortest.",
    speakingExercise: "Sprechübung",
    speakingFirst: "Sprechen zuerst: Nutze zuerst das Mikrofon. Tippen ist nur Backup.",
    generateFollowUp: "Sprech-Nachfrage erzeugen",
    followUpFeedback: "Feedback zur Nachfrage",
    focusAreas: "Fokusbereiche aus deinem Assessment:",
    previousPhase: "Vorherige Phase",
    continueNextPhase: "Zur nächsten Phase",
    finishLesson: "Lektion abschließen",
    error: "Fehler",
    warmupValidation: "Beantworte mindestens 2 Warm-up-Fragen mit einem vollständigen Satz.",
    inputVocabValidation: "Markiere mindestens {n} Wörter als gelernt, bevor du fortfährst.",
    inputCheckValidation: "Fülle den kurzen Input-Check aus, bevor du fortfährst.",
    guidedValidation: "Fülle alle Guided-Practice-Übungen aus.",
    outputMinValidation: "Gib in der Output-Phase eine längere Antwort (mind. 20 Zeichen).",
    outputNeedFollowQuestion: "Erzeuge zuerst die Nachfolgefrage und beantworte sie dann.",
    outputNeedFollowAnswer: "Beantworte die Nachfolgefrage, bevor du fortfährst.",
    feedbackValidation: "Schreibe eine kurze Reflexion, bevor du die Lektion beendest.",
    followupNeedBase: "Gib zuerst deine erste Sprechantwort, bevor du die Nachfolgefrage erzeugst.",
    navHowItWorks: "So funktioniert's",
    navFeatures: "Funktionen",
    navPricing: "Preise",
    navSignIn: "Anmelden",
    navGetStarted: "Loslegen",
    heroGetStartedNow: "Jetzt starten",
    appTitle: "Vlot",
    apiBaseUrl: "API-Basis-URL",
    userId: "Benutzer-ID",
    sessionId: "Sitzungs-ID",
    loadingPlan: "KI erstellt deinen Plan...",
    startOver: "Neu starten",
    skillInsightsTitle: "Skill-Insights",
    coachTipTitle: "COACH-TIPP",
    speakingLoading: "Spricht...",
    readAloud: "Vorlesen",
    recentAchievement: "Jüngster Erfolg",
    learningMetrics: "Lernmetriken",
    reviewDueTodayTitle: "Heute fällige Wiederholung",
    noDueReviews: "Heute keine fälligen Wiederholungen. Starke Konstanz.",
    planTabTitle: "Dein Lernplan",
    currentLevel: "Aktuelles Niveau",
    targetLevel: "Zielniveau",
    duration: "Dauer",
    lessonsDone: "Abgeschlossene Lektionen",
    progressTabTitle: "Dein Fortschritt",
    skillBreakdown: "Skill-Aufschlüsselung",
    lessonHistory: "Lektionsverlauf",
    settingsTitle: "Einstellungen",
    settingsLanguages: "Sprachen",
    settingsISpeak: "Ich spreche",
    settingsImLearning: "Ich lerne",
    settingsTts: "Text-zu-Sprache",
    settingsEnableTts: "TTS aktivieren",
    settingsSpeakingSpeed: "Sprechgeschwindigkeit",
    settingsVoice: "Stimme",
    testVoice: "Stimme testen",
    settingsSession: "Sitzung",
    reset: "Zurücksetzen",
    sidebarCurriculum: "Curriculum",
    sidebarLibrary: "Library",
    sidebarInsights: "Insights",
    sidebarSettings: "Einstellungen",
    lessonSettingsTitle: "Lektionseinstellungen",
    readLessonAloud: "Lektionstext laut vorlesen",
    backToDashboard: "Zurück zum Dashboard",
    currentProgress: "AKTUELLER FORTSCHRITT",
    sessionCompleteTitle: "Sitzung abgeschlossen",
    sessionCompleteBody: "Starker Fortschritt! Du baust mit jeder Lektion mehr Sicherheit und Flüssigkeit auf.",
    levelProgress: "Level-4-Fortschritt",
    xpEarnedLabel: "XP ERHALTEN",
    accuracyLabel: "GENAUIGKEIT",
    nextLesson: "Nächste Lektion",
    reviewMistakes: "Fehler wiederholen",
    privacyPolicy: "Datenschutz",
    termsOfService: "Nutzungsbedingungen",
    contactUs: "Kontakt",
    seeHowItWorks: "So funktioniert's ansehen",
    heroProgressTitle: "Du machst Fortschritte",
    heroProgressSubtitle: "Bereit für deine nächste Sprechlektion.",
    eleganceTitle: "Eleganz in der Bildung",
    quietPersistence: "Stille Ausdauer",
    nextMilestone: "Nächster Meilenstein bei 158 XP",
    quietRewards: "Stille Belohnungen",
    scheduleDemo: "Demo planen",
    risingLearner: "Lernender im Aufstieg",
    level4: "Level 4",
    streakBadge: "4-Tage-Streak - weiter so!",
    totalXp: "Gesamt-XP",
    avgAccuracy: "Ø Genauigkeit",
    reviewsDue: "Fällige Wiederholungen",
    reviewDueTodaySection: "Heute fällige Wiederholung",
    readLessonWordsAloud: "Lektionstext und Wörter laut vorlesen",
    resetSessionDesc: "Setze deine Sitzung zurück und starte ein neues Assessment",
    yourLessons: "Deine Lektionen",
    wordBank: "Wortbank",
    yourProgress: "Dein Fortschritt",
    skillScores: "Skill-Scores",
    learning: "Lernen",
    feedback: "Feedback",
    starterWordsHint: "Starterwörter — nutze sie für die Fragen unten",
    practicedToday: "Was du heute geübt hast",
    sessionStats: "Sitzungsstatistiken",
    xpEarnedInline: "XP erhalten",
    accuracyInline: "Genauigkeit",
    thingsToReview: "Zu wiederholen",
    insteadOf: "Stattdessen:",
    tryLabel: "Versuche:",
    nextLessonFocus: "Worauf möchtest du dich in der nächsten Lektion konzentrieren?",
    level: "Level",
    twitter: "Twitter",
    linkedIn: "LinkedIn",
    heroHeadingPrefix: "Der reife Weg,",
    heroHeadingHighlight: "zu meistern",
    heroHeadingSuffix: "eine neue Sprache",
    journeyTitlePrefix: "Der Weg zu",
    journeyTitleHighlight: "flüssigem Sprechen",
    finalCtaPrefix: "Starte deinen Weg zu",
    finalCtaHighlight: "flüssigem Sprechen",
    finalCtaSuffix: "heute",
    languageFocusTagline: "beginnt mit Fokus.",
    streakDays: "42 Tage",
    youLabel: "DU",
  },
  it: {
    alreadySpeak: "PARLO GIÀ...",
    wantLearn: "VOGLIO IMPARARE...",
    continueJourney: "Continua ->",
    helperText: "Puoi cambiare queste impostazioni in qualsiasi momento dal tuo profilo.",
    onboardingTitle: "Come vuoi iniziare?",
    onboardingDesc:
      "Vuoi iniziare da zero o fare una valutazione per individuare i punti deboli e creare un piano personalizzato?",
    startZero: "Inizia da zero",
    doAssessment: "Fai la valutazione e personalizza il mio piano",
    cancel: "Annulla",
    assessmentStep: "VALUTAZIONE: PASSO",
    of: "DI",
    complete: "Completato",
    assessmentTip: "SUGGERIMENTO: le domande sono mostrate in",
    answerIn: "rispondi in",
    welcomeBack: "Bentornato,",
    readyDaily: "Pronto per il tuo esercizio linguistico quotidiano?",
    plan12w: "Il tuo piano di 3 mesi (12 settimane)",
    viewCalendar: "Vedi calendario",
    locked: "Bloccato",
    completed: "Completato",
    start: "Inizia",
    needSupportLibrary: "Hai bisogno di aiuto? Controlla la scheda Library per vocaboli ed esempi prima di rispondere.",
    speakingExercise: "Esercizio di speaking",
    speakingFirst: "Modalità speaking-first: usa prima il microfono. Scrivere è solo un backup.",
    generateFollowUp: "Genera domanda di follow-up orale",
    followUpFeedback: "Feedback follow-up",
    focusAreas: "Aree di focus dalla tua valutazione:",
    previousPhase: "Fase precedente",
    continueNextPhase: "Continua alla fase successiva",
    finishLesson: "Termina lezione",
    error: "Errore",
    warmupValidation: "Rispondi ad almeno 2 domande warm-up con una frase completa.",
    inputVocabValidation: "Segna almeno {n} parole come apprese prima di continuare.",
    inputCheckValidation: "Compila il breve controllo input prima di continuare.",
    guidedValidation: "Compila tutti gli esercizi di pratica guidata.",
    outputMinValidation: "Dai una risposta più lunga (almeno 20 caratteri) nella fase output.",
    outputNeedFollowQuestion: "Genera prima la domanda di follow-up e poi rispondi.",
    outputNeedFollowAnswer: "Rispondi alla domanda di follow-up prima di continuare.",
    feedbackValidation: "Scrivi una breve riflessione prima di concludere la lezione.",
    followupNeedBase: "Dai prima la tua risposta orale iniziale prima di generare la domanda di follow-up.",
    navHowItWorks: "Come funziona",
    navFeatures: "Funzionalità",
    navPricing: "Prezzi",
    navSignIn: "Accedi",
    navGetStarted: "Inizia",
    heroGetStartedNow: "Inizia ora",
    appTitle: "Vlot",
    apiBaseUrl: "URL base API",
    userId: "ID utente",
    sessionId: "ID sessione",
    loadingPlan: "L'IA sta creando il tuo piano...",
    startOver: "Ricomincia",
    skillInsightsTitle: "Insight competenze",
    coachTipTitle: "CONSIGLIO DEL COACH",
    speakingLoading: "Parlando...",
    readAloud: "Leggi ad alta voce",
    recentAchievement: "Risultato recente",
    learningMetrics: "Metriche di apprendimento",
    reviewDueTodayTitle: "Ripassi di oggi",
    noDueReviews: "Nessun ripasso in scadenza oggi. Ottima costanza.",
    planTabTitle: "Il tuo piano di apprendimento",
    currentLevel: "Livello attuale",
    targetLevel: "Livello obiettivo",
    duration: "Durata",
    lessonsDone: "Lezioni completate",
    progressTabTitle: "I tuoi progressi",
    skillBreakdown: "Dettaglio competenze",
    lessonHistory: "Cronologia lezioni",
    settingsTitle: "Impostazioni",
    settingsLanguages: "Lingue",
    settingsISpeak: "Parlo",
    settingsImLearning: "Sto imparando",
    settingsTts: "Sintesi vocale",
    settingsEnableTts: "Abilita TTS",
    settingsSpeakingSpeed: "Velocità voce",
    settingsVoice: "Voce",
    testVoice: "Testa voce",
    settingsSession: "Sessione",
    reset: "Reset",
    sidebarCurriculum: "Curriculum",
    sidebarLibrary: "Library",
    sidebarInsights: "Insight",
    sidebarSettings: "Impostazioni",
    lessonSettingsTitle: "Impostazioni lezione",
    readLessonAloud: "Leggi ad alta voce il testo della lezione",
    backToDashboard: "Torna alla dashboard",
    currentProgress: "PROGRESSO ATTUALE",
    sessionCompleteTitle: "Sessione completata",
    sessionCompleteBody: "Ottimo progresso! Stai costruendo più fluidità e sicurezza in ogni lezione.",
    levelProgress: "Progresso livello 4",
    xpEarnedLabel: "XP OTTENUTA",
    accuracyLabel: "ACCURATEZZA",
    nextLesson: "Prossima lezione",
    reviewMistakes: "Rivedi errori",
    privacyPolicy: "Privacy policy",
    termsOfService: "Termini di servizio",
    contactUs: "Contatti",
    seeHowItWorks: "Guarda come funziona",
    heroProgressTitle: "Stai facendo progressi",
    heroProgressSubtitle: "Pronto per la tua prossima lezione di speaking.",
    eleganceTitle: "Eleganza nell'educazione",
    quietPersistence: "Costanza silenziosa",
    nextMilestone: "Prossimo traguardo a 158 XP",
    quietRewards: "Ricompense silenziose",
    scheduleDemo: "Prenota una demo",
    risingLearner: "Studente in crescita",
    level4: "Livello 4",
    streakBadge: "streak di 4 giorni - continua così!",
    totalXp: "XP totale",
    avgAccuracy: "Accuratezza media",
    reviewsDue: "Ripassi in scadenza",
    reviewDueTodaySection: "Ripassi di oggi",
    readLessonWordsAloud: "Leggi ad alta voce testo e parole della lezione",
    resetSessionDesc: "Reimposta la sessione ed esegui una nuova valutazione",
    yourLessons: "Le tue lezioni",
    wordBank: "Banca parole",
    yourProgress: "I tuoi progressi",
    skillScores: "Punteggi competenze",
    learning: "Apprendimento",
    feedback: "Feedback",
    starterWordsHint: "Parole iniziali — usale per rispondere alle domande qui sotto",
    practicedToday: "Cosa hai praticato oggi",
    sessionStats: "Statistiche sessione",
    xpEarnedInline: "XP ottenuta",
    accuracyInline: "Accuratezza",
    thingsToReview: "Cose da rivedere",
    insteadOf: "Invece di:",
    tryLabel: "Prova:",
    nextLessonFocus: "Su cosa vuoi concentrarti nella prossima lezione?",
    level: "Livello",
    twitter: "Twitter",
    linkedIn: "LinkedIn",
    heroHeadingPrefix: "Il modo maturo di",
    heroHeadingHighlight: "padroneggiare",
    heroHeadingSuffix: "una nuova lingua",
    journeyTitlePrefix: "Il percorso verso",
    journeyTitleHighlight: "la fluidità",
    finalCtaPrefix: "Inizia il tuo percorso verso",
    finalCtaHighlight: "la fluidità",
    finalCtaSuffix: "oggi",
    languageFocusTagline: "inizia con il focus.",
    streakDays: "42 giorni",
    youLabel: "TU",
  },
  ja: {
    alreadySpeak: "すでに話せる言語...",
    wantLearn: "学びたい言語...",
    continueJourney: "続ける ->",
    helperText: "これらの設定はプロフィールからいつでも変更できます。",
    onboardingTitle: "どのように始めますか？",
    onboardingDesc:
      "ゼロから始めますか？それとも評価を行って弱点を見つけ、個別プランを作成しますか？",
    startZero: "ゼロから始める",
    doAssessment: "評価してプランを最適化する",
    cancel: "キャンセル",
    assessmentStep: "評価: ステップ",
    of: "/",
    complete: "完了",
    assessmentTip: "ヒント: 質問は",
    answerIn: "で表示、回答は",
    welcomeBack: "おかえりなさい、",
    readyDaily: "今日の語学トレーニングを始めましょうか？",
    plan12w: "あなたの3か月プラン（12週間）",
    viewCalendar: "カレンダーを見る",
    locked: "ロック中",
    completed: "完了",
    start: "開始",
    needSupportLibrary: "サポートが必要ですか？回答前に Library タブで語彙と例文を確認しましょう。",
    speakingExercise: "スピーキング練習",
    speakingFirst: "スピーキング優先モード: まずマイクを使ってください。入力は補助です。",
    generateFollowUp: "フォローアップ質問を生成",
    followUpFeedback: "フォローアップのフィードバック",
    focusAreas: "評価からの重点項目:",
    previousPhase: "前のフェーズ",
    continueNextPhase: "次のフェーズへ",
    finishLesson: "レッスン完了",
    error: "エラー",
    warmupValidation: "ウォームアップは少なくとも2問、完全な文で回答してください。",
    inputVocabValidation: "続行前に少なくとも {n} 語を「理解した」にしてください。",
    inputCheckValidation: "続行前に短い input チェックを入力してください。",
    guidedValidation: "ガイド付き練習をすべて入力してください。",
    outputMinValidation: "output フェーズでは20文字以上の回答を入力してください。",
    outputNeedFollowQuestion: "先にフォローアップ質問を生成してから回答してください。",
    outputNeedFollowAnswer: "続行する前にフォローアップ質問へ回答してください。",
    feedbackValidation: "レッスン終了前に短い振り返りを書いてください。",
    followupNeedBase: "フォローアップ質問を生成する前に、最初の発話回答を入力してください。",
    navHowItWorks: "使い方",
    navFeatures: "機能",
    navPricing: "料金",
    navSignIn: "サインイン",
    navGetStarted: "はじめる",
    heroGetStartedNow: "今すぐ開始",
    appTitle: "Vlot",
    apiBaseUrl: "APIベースURL",
    userId: "ユーザーID",
    sessionId: "セッションID",
    loadingPlan: "AIが学習プランを作成中...",
    startOver: "最初からやり直す",
    skillInsightsTitle: "スキル分析",
    coachTipTitle: "コーチのヒント",
    speakingLoading: "読み上げ中...",
    readAloud: "音読する",
    recentAchievement: "最近の達成",
    learningMetrics: "学習メトリクス",
    reviewDueTodayTitle: "今日の復習",
    noDueReviews: "今日の復習はありません。素晴らしい継続です。",
    planTabTitle: "あなたの学習プラン",
    currentLevel: "現在のレベル",
    targetLevel: "目標レベル",
    duration: "期間",
    lessonsDone: "完了レッスン",
    progressTabTitle: "あなたの進捗",
    skillBreakdown: "スキル内訳",
    lessonHistory: "レッスン履歴",
    settingsTitle: "設定",
    settingsLanguages: "言語",
    settingsISpeak: "話せる言語",
    settingsImLearning: "学習中の言語",
    settingsTts: "音声読み上げ",
    settingsEnableTts: "TTSを有効化",
    settingsSpeakingSpeed: "読み上げ速度",
    settingsVoice: "音声",
    testVoice: "音声テスト",
    settingsSession: "セッション",
    reset: "リセット",
    sidebarCurriculum: "カリキュラム",
    sidebarLibrary: "Library",
    sidebarInsights: "分析",
    sidebarSettings: "設定",
    lessonSettingsTitle: "レッスン設定",
    readLessonAloud: "レッスン文を音読する",
    backToDashboard: "ダッシュボードへ戻る",
    currentProgress: "現在の進捗",
    sessionCompleteTitle: "セッション完了",
    sessionCompleteBody: "素晴らしい進捗です！毎回のレッスンで流暢さと自信が高まっています。",
    levelProgress: "レベル4進捗",
    xpEarnedLabel: "獲得XP",
    accuracyLabel: "正確性",
    nextLesson: "次のレッスン",
    reviewMistakes: "間違いを復習",
    privacyPolicy: "プライバシーポリシー",
    termsOfService: "利用規約",
    contactUs: "お問い合わせ",
    seeHowItWorks: "使い方を見る",
    heroProgressTitle: "あなたは着実に進歩しています",
    heroProgressSubtitle: "次のスピーキングレッスンの準備はできています。",
    eleganceTitle: "学びの美しさ",
    quietPersistence: "静かな継続",
    nextMilestone: "次のマイルストーンまで158 XP",
    quietRewards: "静かな報酬",
    scheduleDemo: "デモを予約",
    risingLearner: "成長中の学習者",
    level4: "レベル4",
    streakBadge: "4日連続 - この調子！",
    totalXp: "合計XP",
    avgAccuracy: "平均正確性",
    reviewsDue: "復習予定",
    reviewDueTodaySection: "今日の復習",
    readLessonWordsAloud: "レッスンの文章と単語を音読する",
    resetSessionDesc: "セッションをリセットして新しい評価を始めます",
    yourLessons: "あなたのレッスン",
    wordBank: "単語バンク",
    yourProgress: "あなたの進捗",
    skillScores: "スキルスコア",
    learning: "学習",
    feedback: "フィードバック",
    starterWordsHint: "スターター単語 — 下の質問に答えるために使ってください",
    practicedToday: "今日練習した内容",
    sessionStats: "セッション統計",
    xpEarnedInline: "獲得XP",
    accuracyInline: "正確性",
    thingsToReview: "復習ポイント",
    insteadOf: "次の代わりに:",
    tryLabel: "こちらを試す:",
    nextLessonFocus: "次のレッスンで何に集中しますか？",
    level: "レベル",
    twitter: "Twitter",
    linkedIn: "LinkedIn",
    heroHeadingPrefix: "大人の学び方で",
    heroHeadingHighlight: "習得する",
    heroHeadingSuffix: "新しい言語を",
    journeyTitlePrefix: "目指す旅は",
    journeyTitleHighlight: "流暢さ",
    finalCtaPrefix: "あなたの",
    finalCtaHighlight: "流暢さ",
    finalCtaSuffix: "への旅を今日始めよう",
    languageFocusTagline: "集中から始まる。",
    streakDays: "42日間",
    youLabel: "あなた",
  },
};
const ui = computed(() => ({
  ...uiTextBySpeak.en,
  ...(uiTextBySpeak[selectedSpeakCode.value] || {}),
}));
function t(key, vars = {}) {
  let text = ui.value[key] || uiTextBySpeak.en[key] || key;
  for (const [k, v] of Object.entries(vars)) {
    text = text.replaceAll(`{${k}}`, String(v));
  }
  return text;
}

const promptTemplatesBySpeak = {
  en: [
    "Great start. Please tell me your name and why you want to learn {learn}. Answer in {learn}.",
    "Nice. Where are you from, and when do you want to use {learn}? Answer in {learn}.",
    "What are your hobbies? Please answer in {learn}.",
    "Final question: describe what you did today using complete sentences in {learn}.",
  ],
  nl: [
    "Goede start. Vertel je naam en waarom je {learn} wilt leren. Antwoord in het {learn}.",
    "Mooi. Waar kom je vandaan, en wanneer wil je {learn} gebruiken? Antwoord in het {learn}.",
    "Wat zijn je hobby's? Antwoord in het {learn}.",
    "Laatste vraag: beschrijf wat je vandaag hebt gedaan met volledige zinnen in het {learn}.",
  ],
  es: [
    "Buen comienzo. Dime tu nombre y por que quieres aprender {learn}. Responde en {learn}.",
    "Muy bien. De donde eres y cuando quieres usar {learn}? Responde en {learn}.",
    "Cuales son tus pasatiempos? Responde en {learn}.",
    "Ultima pregunta: describe lo que hiciste hoy con oraciones completas en {learn}.",
  ],
  fr: [
    "Tres bon debut. Dis ton nom et pourquoi tu veux apprendre {learn}. Reponds en {learn}.",
    "Bien. D'ou viens-tu et quand veux-tu utiliser {learn} ? Reponds en {learn}.",
    "Quels sont tes loisirs ? Reponds en {learn}.",
    "Derniere question : decris ce que tu as fait aujourd'hui avec des phrases completes en {learn}.",
  ],
  de: [
    "Guter Start. Nenne deinen Namen und warum du {learn} lernen willst. Antworte auf {learn}.",
    "Super. Woher kommst du und wann willst du {learn} nutzen? Antworte auf {learn}.",
    "Was sind deine Hobbys? Bitte antworte auf {learn}.",
    "Letzte Frage: Beschreibe, was du heute gemacht hast, mit ganzen Satzen auf {learn}.",
  ],
  it: [
    "Ottimo inizio. Dimmi il tuo nome e perche vuoi imparare {learn}. Rispondi in {learn}.",
    "Bene. Da dove vieni e quando vuoi usare {learn}? Rispondi in {learn}.",
    "Quali sono i tuoi hobby? Rispondi in {learn}.",
    "Ultima domanda: descrivi cosa hai fatto oggi con frasi complete in {learn}.",
  ],
  ja: [
    "良いスタートです。名前と、なぜ{learn}を学びたいか教えてください。{learn}で答えてください。",
    "いいですね。どこの出身ですか。いつ{learn}を使いたいですか。{learn}で答えてください。",
    "趣味は何ですか。{learn}で答えてください。",
    "最後の質問です。今日したことを{learn}で完全な文で説明してください。",
  ],
};
const totalAssessmentSteps = 4;

const form = reactive({
  user_id: "demo-user",
  session_id: "session-1",
  answer1: "",
  answer2: "",
  answer3: "",
  answer4: "",
});
const completedWeekNumbers = ref([]);
const lessonResponses = reactive({
  warm_up: ["", "", ""],
  input_vocab_checks: [],
  input_check: "",
  guided_practice: ["", "", ""],
  output_speaking: "",
  feedback_reflection: "",
});
const outputFollowUpQuestion = ref("");
const outputFollowUpAnswer = ref("");
const outputUsedSpeech = ref(false);
const outputFollowUpUsedSpeech = ref(false);
const phaseValidationError = ref("");
const lessonSidebarTab = ref("curriculum");
const settingsTtsEnabled = ref(true);
const settingsPlaybackRate = ref(180);
const dashboardTab = ref("home");
const sttActive = ref(false);
let sttRecognizer = null;
const availableVoices = ref([]);
const selectedVoiceURI = ref("");

const ttsLangCodeMap = {
  fr: "fr-FR", nl: "nl-NL", es: "es-ES", de: "de-DE",
  en: "en-US", ja: "ja-JP", hi: "hi-IN",
};
const ttsDefaultVoiceHintsByLang = {
  en: ["siri", "samantha", "allison", "ava", "serena", "aria", "guy", "zira", "david"],
  nl: ["xander", "femke", "claire", "colette", "maarten", "siri"],
  es: ["jorge", "monica", "paulina", "elvira", "alvaro", "siri"],
  fr: ["thomas", "amelie", "denise", "henri", "siri"],
  de: ["anna", "markus", "katja", "conrad", "siri"],
  it: ["alice", "luca", "isabella", "diego", "siri"],
  ja: ["kyoko", "otoya", "nanami", "keita", "siri"],
  hi: ["swara", "kabir", "madhur", "siri"],
};
const ttsLangCode = computed(
  () => ttsLangCodeMap[selectedLearnCode.value] || "en-US",
);
const voicesForLanguage = computed(() => {
  const prefix = ttsLangCode.value.split("-")[0];
  return availableVoices.value.filter((v) => v.lang.startsWith(prefix));
});

const answerKeys = ["answer1", "answer2", "answer3", "answer4"];
const canStartJourney = computed(
  () => Boolean(selectedSpeakCode.value) && Boolean(selectedLearnCode.value),
);
const currentSpeakingLanguage = computed(
  () =>
    speakLanguages.find((language) => language.code === selectedSpeakCode.value)
      ?.label || "English",
);
const currentLearningLanguage = computed(
  () =>
    learnLanguages.find((language) => language.code === selectedLearnCode.value)
      ?.label || "French",
);
const assessmentPrompts = computed(() => {
  const templates =
    promptTemplatesBySpeak[selectedSpeakCode.value] || promptTemplatesBySpeak.en;
  return templates.map((template) =>
    template.replaceAll("{learn}", currentLearningLanguage.value),
  );
});
const showLanding = computed(() => currentPath.value === "/");
const showLanguagePicker = computed(
  () => currentPath.value === "/onboarding/languages",
);
const showAssessmentRoute = computed(
  () => currentPath.value === "/onboarding/assessment",
);
const showDashboard = computed(() => currentPath.value === "/dashboard");
const inAssessment = computed(
  () => showAssessmentRoute.value && step.value >= 1 && step.value <= 4,
);
const assessmentProgress = computed(() =>
  Math.min(100, Math.round((step.value / totalAssessmentSteps) * 100)),
);
const responsePlaceholder = computed(
  () => `${t("answerIn")} ${currentLearningLanguage.value}...`,
);
const assessmentMessages = computed(() => {
  if (!inAssessment.value) return [];
  const messages = [];
  for (let i = 0; i < step.value; i += 1) {
    messages.push({
      role: "coach",
      text: assessmentPrompts.value[i],
      meta: i === step.value - 1 ? "VLOT AI  -  JUST NOW" : "VLOT AI",
    });
    const key = answerKeys[i];
    const answer = key ? form[key].trim() : "";
    if (answer) {
      messages.push({
        role: "user",
        text: answer,
        meta: "YOU",
      });
    }
  }
  return messages;
});
const currentAnswer = computed({
  get() {
    const key = answerKeys[step.value - 1];
    return key ? form[key] : "";
  },
  set(value) {
    const key = answerKeys[step.value - 1];
    if (key) form[key] = value;
  },
});
const levelLabelMap = {
  A1: "Beginner",
  A2: "Elementary",
  B1: "Intermediate",
  B2: "Upper Intermediate",
};
const learnerLevelLabel = computed(() => {
  const level = result.value?.assessment?.level;
  return level ? `${level} - ${levelLabelMap[level] || "Learner"}` : "A2 - Elementary";
});
const lessonTemplatePhases = [
  {
    phase: "warm_up",
    duration_minutes: 8,
    goal: "Activate prior knowledge and retrieve key items from the previous lesson.",
    teacher_actions: [
      "Ask 2-3 short recall questions.",
      "Request three simple sentences using the previous structure.",
    ],
    learner_actions: [
      "Answer immediately without notes.",
      "Produce short spoken or written responses.",
    ],
  },
  {
    phase: "input",
    duration_minutes: 12,
    goal: "Introduce one new concept in context.",
    teacher_actions: [
      "Teach 5-8 words or one grammar rule in sample sentences.",
      "Give one quick comprehension check.",
    ],
    learner_actions: [
      "Read and repeat the model sentences.",
      "Identify meaning and form in context.",
    ],
  },
  {
    phase: "guided_practice",
    duration_minutes: 12,
    goal: "Apply the new concept in controlled tasks.",
    teacher_actions: [
      "Run sentence completion and fill-in tasks.",
      "Correct high-impact errors immediately.",
    ],
    learner_actions: [
      "Complete short controlled exercises.",
      "Rewrite corrected examples once.",
    ],
  },
  {
    phase: "output_speaking",
    duration_minutes: 18,
    goal: "Use the language in realistic production.",
    teacher_actions: [
      "Start a roleplay or short storytelling prompt.",
      "Keep tutor talk minimal so learner speaks most of the time.",
    ],
    learner_actions: [
      "Speak for most of the phase using full sentences.",
      "Respond to follow-up prompts naturally.",
    ],
  },
  {
    phase: "feedback_correction",
    duration_minutes: 8,
    goal: "Consolidate learning with focused correction.",
    teacher_actions: [
      "Highlight only major recurring mistakes.",
      "Model correct forms and quick recap.",
    ],
    learner_actions: [
      "Repeat corrected sentences.",
      "Note one improvement goal for next session.",
    ],
  },
];

const lessonOutlineForSession = computed(() => {
  const fromCurriculum = activeLesson.value?.phases;
  if (Array.isArray(fromCurriculum) && fromCurriculum.length === 5) return fromCurriculum;
  const generated = result.value?.tutor_output?.lesson_outline;
  if (Array.isArray(generated) && generated.length === 5) return generated;
  return lessonTemplatePhases;
});
const isFirstLessonSession = computed(() => {
  const week = Number(activeLesson.value?.week || 0);
  const lessonNumber = Number(activeLesson.value?.lesson_number || 0);
  return week === 1 && lessonNumber === 1 && completedWeekNumbers.value.length === 0;
});
const effectiveLessonOutline = computed(() => {
  if (!isFirstLessonSession.value) return lessonOutlineForSession.value;
  const phases = lessonOutlineForSession.value.map((phase) => ({ ...phase }));
  if (!phases.length) return phases;
  phases[0] = {
    ...phases[0],
    goal: "Zero-pressure first contact — just try, any attempt is great.",
    teacher_actions: [
      "Do a short check-in and model 1-2 very simple examples.",
      "Ask the learner to produce basic introduction lines.",
    ],
    learner_actions: [
      "Repeat and adapt simple model sentences.",
      "Introduce yourself with short, clear sentences.",
    ],
  };
  return phases;
});
const currentLessonPhase = computed(
  () => effectiveLessonOutline.value[activePhaseIndex.value] || effectiveLessonOutline.value[0],
);
const phaseProgressPercent = computed(() =>
  Math.round(((activePhaseIndex.value + 1) / Math.max(1, effectiveLessonOutline.value.length)) * 100),
);
const phaseTitleMap = {
  warm_up: "Warm-up",
  input: "New vocabulary",
  guided_practice: "Practice exercises",
  output_speaking: "Speaking practice",
  feedback_correction: "Lesson complete!",
};
const phaseSubtitleMap = {
  warm_up: "Recall what you know — short answers are fine.",
  input: "Read through the new words and phrases for this lesson.",
  guided_practice: "Apply what you just learned in short, focused exercises.",
  output_speaking: "Use the language in a realistic scenario.",
  feedback_correction: "Here is what you practiced and what to improve next time.",
};
const currentPhaseTitle = computed(() => {
  if (isFirstLessonSession.value && currentLessonPhase.value?.phase === "warm_up") {
    return "First lesson check-in";
  }
  return phaseTitleMap[currentLessonPhase.value?.phase] || "Lesson phase";
});
const vocabularyTerms = computed(() => {
  return inputVocabularyItems.value.map(
    (item) => `${item.term} - ${item.meaning}`,
  );
});
const assessmentWeakAreas = computed(() => result.value?.assessment?.weak_areas || []);
const assessmentStrongAreas = computed(() => result.value?.assessment?.strong_areas || []);
const aiTutorMessage = computed(
  () =>
    result.value?.tutor_output?.tutor_message ||
    "Let's continue with a focused and practical session.",
);
const aiSuggestedExercise = computed(
  () =>
    result.value?.tutor_output?.suggested_exercise ||
    "Complete one short exercise that applies today's focus.",
);
const aiMemoryNote = computed(
  () => result.value?.tutor_output?.memory_note || "Track one key improvement for next session.",
);
const phaseTeacherActions = computed(
  () => currentLessonPhase.value?.teacher_actions || [],
);
const phaseLearnerActions = computed(
  () => currentLessonPhase.value?.learner_actions || [],
);
const dynamicWarmupPrompt = computed(() => {
  if (isFirstLessonSession.value) {
    return `Welcome to your first ${currentLearningLanguage.value} lesson! Just give it a try — there are no wrong answers here. Write whatever comes to mind.`;
  }
  const weak = assessmentWeakAreas.value[0];
  if (weak) {
    return `Warm-up focus: quickly activate your previous learning around "${weak}" with short recall answers.`;
  }
  return "Warm-up focus: answer quickly in full sentences to activate recall.";
});
const outputScenario = computed(() => {
  const lessonTitle = activeLesson.value?.title || activeLesson.value?.focus || "today's topic";
  if (isFirstLessonSession.value) {
    return `Question: Introduce yourself in ${currentLearningLanguage.value}. Say your name, where you are from, and one hobby.`;
  }
  if (currentLessonPhase.value?.scenario_prompt) {
    const prompt = String(currentLessonPhase.value.scenario_prompt).trim();
    if (prompt.toLowerCase().startsWith("question:")) return prompt;
    return `Question: ${prompt}`;
  }
  return `Question: Answer in ${currentLearningLanguage.value}. Talk about "${lessonTitle}" and use 1-2 words from this lesson.`;
});
const speakingFocusWords = computed(() =>
  inputVocabularyItems.value
    .slice(0, 5)
    .map((item) => item.term)
    .filter((term) => typeof term === "string" && term.trim().length > 0),
);
const outputPrimaryFeedback = computed(() => {
  const text = lessonResponses.output_speaking.trim();
  if (!text) return "";
  const words = text.split(/\s+/).filter(Boolean);
  const lowered = text.toLowerCase();
  const usedTerms = speakingFocusWords.value.filter((term) =>
    lowered.includes(String(term).toLowerCase()),
  );
  if (words.length < 8) {
    return "Good start. Expand your answer to 2-3 full sentences and include at least one target word.";
  }
  if (!usedTerms.length) {
    return "Nice effort. Now strengthen it by using 1-2 words from this lesson's vocabulary.";
  }
  return `Strong response. Great use of: ${usedTerms.slice(0, 2).join(", ")}.`;
});
const outputFollowUpFeedback = computed(() => {
  const text = outputFollowUpAnswer.value.trim();
  if (!text) return "";
  const words = text.split(/\s+/).filter(Boolean);
  const lowered = text.toLowerCase();
  const usedTerms = speakingFocusWords.value.filter((term) =>
    lowered.includes(String(term).toLowerCase()),
  );
  if (words.length < 6) {
    return "Good attempt. Try one longer sentence with more detail.";
  }
  if (!usedTerms.length) {
    return "Good answer. For higher score, include one lesson word from the Library.";
  }
  return `Great follow-up answer. You used lesson vocabulary well (${usedTerms.slice(0, 2).join(", ")}).`;
});
const inputVocabularyItems = computed(() => {
  // 1. AI-generated vocab from the lesson design (best case)
  const fromAi = currentLessonPhase.value?.vocab_selection;
  if (Array.isArray(fromAi) && fromAi.length) {
    return fromAi.map((item) => ({
      term: item.term,
      meaning: item.meaning,
      example_sentence: item.example_sentence,
    }));
  }
  // 2. Exercise list attached to the lesson (Bot 4 fallback)
  const exercises = (activeLesson.value?.exercises || []).filter(
    (e) => typeof e === "string" && e.trim().length > 0,
  ).slice(0, 6);
  if (exercises.length) {
    return exercises.map((exercise, idx) => ({
      term: exercise,
      meaning: `Exercise ${idx + 1}`,
      example_sentence: "",
    }));
  }
  // 3. First lesson → show the starter vocabulary so the learner always has words
  if (isFirstLessonSession.value) {
    return starterVocabForLanguage.value.map((item) => ({
      term: item.term,
      meaning: item.meaning,
      example_sentence: `Try using "${item.term}" in a short sentence.`,
    }));
  }
  // 4. Other lessons without AI vocab → derive 4 placeholder items from the lesson title/focus
  const focus = activeLesson.value?.title || activeLesson.value?.focus || currentLessonPhase.value?.goal || "";
  const words = focus.split(/\s+/).filter((w) => w.length > 3).slice(0, 4);
  if (words.length) {
    return words.map((w) => ({
      term: w,
      meaning: `Key word for this lesson`,
      example_sentence: `Use "${w}" in a sentence about today's topic.`,
    }));
  }
  return [];
});
const knownWordCount = computed(
  () => lessonResponses.input_vocab_checks.filter(Boolean).length,
);

const starterVocabByLanguage = {
  fr: [
    { term: "Bonjour", meaning: "Hello" },
    { term: "Merci", meaning: "Thank you" },
    { term: "Oui / Non", meaning: "Yes / No" },
    { term: "Je m'appelle …", meaning: "My name is …" },
    { term: "S'il vous plaît", meaning: "Please" },
    { term: "Au revoir", meaning: "Goodbye" },
  ],
  nl: [
    { term: "Hallo", meaning: "Hello" },
    { term: "Dankjewel", meaning: "Thank you" },
    { term: "Ja / Nee", meaning: "Yes / No" },
    { term: "Ik heet …", meaning: "My name is …" },
    { term: "Alsjeblieft", meaning: "Please" },
    { term: "Tot ziens", meaning: "Goodbye" },
  ],
  es: [
    { term: "Hola", meaning: "Hello" },
    { term: "Gracias", meaning: "Thank you" },
    { term: "Sí / No", meaning: "Yes / No" },
    { term: "Me llamo …", meaning: "My name is …" },
    { term: "Por favor", meaning: "Please" },
    { term: "Adiós", meaning: "Goodbye" },
  ],
  de: [
    { term: "Hallo", meaning: "Hello" },
    { term: "Danke", meaning: "Thank you" },
    { term: "Ja / Nein", meaning: "Yes / No" },
    { term: "Ich heiße …", meaning: "My name is …" },
    { term: "Bitte", meaning: "Please" },
    { term: "Auf Wiedersehen", meaning: "Goodbye" },
  ],
  en: [
    { term: "Hello", meaning: "Hallo" },
    { term: "Thank you", meaning: "Dankjewel" },
    { term: "Yes / No", meaning: "Ja / Nee" },
    { term: "My name is …", meaning: "Mijn naam is …" },
    { term: "Please", meaning: "Alsjeblieft" },
    { term: "Goodbye", meaning: "Tot ziens" },
  ],
  ja: [
    { term: "こんにちは", meaning: "Hello (Konnichiwa)" },
    { term: "ありがとう", meaning: "Thank you (Arigatou)" },
    { term: "はい / いいえ", meaning: "Yes / No (Hai / Iie)" },
    { term: "私は〜です", meaning: "My name is … (Watashi wa ~ desu)" },
    { term: "おねがいします", meaning: "Please (Onegaishimasu)" },
    { term: "さようなら", meaning: "Goodbye (Sayounara)" },
  ],
  hi: [
    { term: "नमस्ते", meaning: "Hello (Namaste)" },
    { term: "धन्यवाद", meaning: "Thank you (Dhanyavaad)" },
    { term: "हाँ / नहीं", meaning: "Yes / No (Haan / Nahin)" },
    { term: "मेरा नाम है …", meaning: "My name is … (Mera naam hai)" },
    { term: "कृपया", meaning: "Please (Kripaya)" },
    { term: "अलविदा", meaning: "Goodbye (Alvida)" },
  ],
};
const starterVocabForLanguage = computed(() => {
  const learnCode = selectedLearnCode.value;
  if (learnCode !== "en") {
    return starterVocabByLanguage[learnCode] || starterVocabByLanguage.fr;
  }
  // Learning English: invert native-language vocab so the English word is the term
  // and the native translation is the meaning.
  const nativeVocab = starterVocabByLanguage[selectedSpeakCode.value];
  if (nativeVocab) {
    return nativeVocab.map((item) => ({ term: item.meaning, meaning: item.term }));
  }
  return starterVocabByLanguage.en;
});

const lessonLibraryVocab = computed(() => {
  const vocab = [];
  for (const lesson of curriculumLessons.value) {
    const phases = lesson.phases || [];
    for (const phase of phases) {
      if (phase.phase === "input" && Array.isArray(phase.vocab_selection)) {
        for (const item of phase.vocab_selection) {
          vocab.push({
            term: item.term,
            meaning: item.meaning,
            example: item.example_sentence || "",
            lessonTitle: lesson.title || `Week ${lesson.week}`,
          });
        }
      }
    }
  }
  if (!vocab.length) {
    return inputVocabularyItems.value.map((item) => ({
      term: item.term,
      meaning: item.meaning,
      example: item.example_sentence || "",
      lessonTitle: activeLesson.value?.title || "Current lesson",
    }));
  }
  return vocab;
});

const completedLessonsCount = computed(
  () => curriculumLessons.value.filter((l) => l.completed).length,
);
const totalXpEarned = computed(() =>
  curriculumLessons.value
    .filter((l) => l.completed)
    .reduce((sum, l) => sum + Number(l.xp_earned || l.xp || 60), 0),
);

const warmupQuestions = computed(() => {
  const weak = assessmentWeakAreas.value;
  if (isFirstLessonSession.value) {
    const vocab = starterVocabForLanguage.value;
    const hello = vocab[0]?.term || "Hello";
    const myName = vocab[3]?.term || "My name is …";
    return [
      `Use "${hello}" to write a short greeting.`,
      `Try writing "${myName}" and fill in your name.`,
      `Pick any word from the word bank above and write one sentence with it — any attempt is great!`,
    ];
  }
  // Use previous lesson vocab for contextual recall
  const prevLesson = activeLessonIndex.value > 0
    ? curriculumLessons.value[activeLessonIndex.value - 1]
    : null;
  const prevVocab = prevLesson?.phases
    ?.find((p) => p.phase === "input")
    ?.vocab_selection || [];
  const prevTerm = prevVocab[0]?.term;
  const prevTerm2 = prevVocab[1]?.term;

  // Supplement with words not yet mastered
  const unknown = getUnknownVocab();
  const unknownTerm = unknown.find((w) => !prevVocab.some((v) => v.term === w.term))?.term;

  return [
    prevTerm
      ? `Recall from last time: write a sentence using "${prevTerm}".`
      : `Write one sentence that practises: ${weak[0] || "sentence flow"}.`,
    prevTerm2
      ? `Can you also use "${prevTerm2}" in a short sentence?`
      : `Write one sentence that practises: ${weak[1] || "clear vocabulary use"}.`,
    unknownTerm
      ? `You didn't fully learn "${unknownTerm}" last time — try it in a sentence now.`
      : "Write one complete sentence about what you did yesterday.",
  ];
});
const guidedExercisePrompts = computed(() => {
  // 1. AI-generated exercises from Bot 4 — best case
  const aiTasks = currentLessonPhase.value?.guided_tasks;
  if (Array.isArray(aiTasks) && aiTasks.length) {
    return aiTasks.map((task) => ({
      prompt: task.prompt,
      sentence_with_blank: task.sentence_with_blank || "",
      hint: task.hint || "",
    }));
  }

  // 2. Build exercises from the vocabulary the learner just saw in the input phase
  const vocab = inputVocabularyItems.value;
  if (vocab.length >= 2) {
    const v0 = vocab[0];
    const v1 = vocab[1];
    const v2 = vocab[Math.min(2, vocab.length - 1)];
    return [
      {
        prompt: `Fill in the blank: which word means "${v0.meaning}"?`,
        sentence_with_blank: `The word for "${v0.meaning}" in ${currentLearningLanguage.value} is: ___`,
        hint: `You just saw this word in the list above. It is: ${v0.term}`,
      },
      {
        prompt: `Write "${v1.meaning}" in ${currentLearningLanguage.value}.`,
        sentence_with_blank: "",
        hint: `The word is: ${v1.term}`,
      },
      {
        prompt: `Write a short sentence (2–5 words) using "${v2.term}" (${v2.meaning}).`,
        sentence_with_blank: "",
        hint: v2.example_sentence
          ? `Example: ${v2.example_sentence}`
          : `Start your sentence with "${v2.term} ..."`,
      },
    ];
  }

  // 3. No vocab available at all — show simple beginner exercises for the target language
  const lang = currentLearningLanguage.value;
  const starter = starterVocabForLanguage.value;
  const hello = starter[0]?.term || "Hello";
  const myName = starter[3]?.term || "My name is …";
  const thanks = starter[1]?.term || "Thank you";
  return [
    {
      prompt: `Write a greeting in ${lang}.`,
      sentence_with_blank: "",
      hint: `Use: ${hello}`,
    },
    {
      prompt: `Introduce yourself in one sentence in ${lang}.`,
      sentence_with_blank: "",
      hint: `Use: ${myName}`,
    },
    {
      prompt: `How do you say "Thank you" in ${lang}? Write it in a sentence.`,
      sentence_with_blank: "",
      hint: `The word is: ${thanks}`,
    },
  ];
});
const dashboardMetrics = computed(() => dashboardData.value?.metrics || null);
const reviewDueToday = computed(() =>
  Array.isArray(dashboardData.value?.review_due_today)
    ? dashboardData.value.review_due_today
    : [],
);
const grammarTipMap = {
  "sentence flow": "Keep subjects and verbs close together. Use connectors like 'and', 'but', 'because' to build longer ideas.",
  "vocabulary": "Try to use each new word in at least two different sentences — once to understand it, once to produce it yourself.",
  "grammar": "Check that verb forms agree with their subject (I go, she goes). One error repeated is easier to fix than many different ones.",
  "tense": "Choose your tense before you start the sentence. Past = finished. Present = happening now. Future = not yet.",
  "articles": "Use 'a' for something new or general. Use 'the' when both you and the listener know which one you mean.",
  "pronunciation": "Slow down slightly and stress the key word in each sentence. Clarity beats speed every time.",
  "speaking confidence": "Speak at a steady pace. A short pause before answering is normal and sounds more natural than rushing.",
  "word order": "In most sentences: Subject → Verb → Object. Adverbs usually go before the verb or at the end.",
  "prepositions": "Learn prepositions in fixed phrases (at the weekend, in the morning, on Monday) — they rarely follow logic.",
};

const feedbackCorrections = computed(() => {
  const weak = assessmentWeakAreas.value;
  if (!weak.length) {
    return [
      {
        before: "I speak very fast",
        correction: "I speak very quickly and clearly",
        note: "Add precision markers to improve clarity.",
        why: grammarTipMap["speaking confidence"],
      },
    ];
  }
  return weak.slice(0, 2).map((topic) => {
    const lowerTopic = topic.toLowerCase();
    const why =
      Object.entries(grammarTipMap).find(([key]) => lowerTopic.includes(key))?.[1] ||
      `Practise "${topic}" consistently — use it in three different sentences each day.`;
    return {
      before: `Inconsistent use around "${topic}"`,
      correction: `Apply a corrected form consistently for "${topic}"`,
      note: "Repeat corrected examples 3 times aloud.",
      why,
    };
  });
});

const curriculumLessons = computed(() => {
  const persistedLessons = Array.isArray(dashboardData.value?.curriculum_lessons)
    ? dashboardData.value.curriculum_lessons
    : Array.isArray(dashboardData.value?.lessons)
      ? dashboardData.value.lessons
      : [];
  if (persistedLessons.length) {
    const sortedLessons = [...persistedLessons].sort((a, b) => {
      const aSeq = Number(a.sequence_index || 0);
      const bSeq = Number(b.sequence_index || 0);
      if (aSeq !== bSeq) return aSeq - bSeq;
      const aWeek = Number(a.week || 0);
      const bWeek = Number(b.week || 0);
      if (aWeek !== bWeek) return aWeek - bWeek;
      return Number(a.lesson_number || 0) - Number(b.lesson_number || 0);
    });

    const normalized = sortedLessons.map((lesson, index) => ({
      ...lesson,
      id: lesson.lesson_id || `W${lesson.week}-L${lesson.lesson_number || 1}`,
      title: lesson.title || lesson.focus || `Lesson ${index + 1}`,
      dayLabel: `WEEK ${lesson.week} · LESSON ${lesson.lesson_number || 1}`,
      minutes: Number(lesson.estimated_minutes || 50),
      xp: Number(lesson.xp_earned || 60),
      persistedStatus: String(lesson.status || "not_started"),
      index,
    }));

    return normalized.map((lesson, index) => {
      const previous = index > 0 ? normalized[index - 1] : null;
      const completed = lesson.persistedStatus === "completed";
      const lockedByFlow = Boolean(previous && previous.persistedStatus !== "completed" && !completed);
      return {
        ...lesson,
        completed,
        locked: lesson.persistedStatus === "locked" || lockedByFlow,
      };
    });
  }
  const goals = result.value?.plan?.weekly_goals || [];
  const firstIncompleteWeek =
    goals.find((goal) => !completedWeekNumbers.value.includes(Number(goal.week)))?.week ??
    goals.length + 1;
  return goals.map((goal, index) => ({
    id: `W${goal.week}-L1`,
    lesson_id: `W${goal.week}-L1`,
    week: goal.week,
    lesson_number: 1,
    dayLabel: `WEEK ${goal.week} · LESSON 1`,
    title: goal.focus,
    minutes: 50,
    xp: 60,
    locked: Number(goal.week) > Number(firstIncompleteWeek),
    completed: completedWeekNumbers.value.includes(Number(goal.week)),
    persistedStatus: "not_started",
    phases: lessonTemplatePhases,
    index,
  }));
});

const activeLesson = computed(() => {
  const lessons = curriculumLessons.value;
  if (!lessons.length) return null;
  const safeIndex = Math.max(0, Math.min(activeLessonIndex.value, lessons.length - 1));
  return lessons[safeIndex] || null;
});

const weeklyLessons = computed(() => {
  return curriculumLessons.value;
});
const progressNavItems = computed(() => [
  { key: "home", label: t("navHowItWorks"), icon: "⌂" },
  { key: "plan", label: t("planTabTitle"), icon: "▤" },
  { key: "progress", label: t("progressTabTitle"), icon: "◫" },
  { key: "settings", label: t("settingsTitle"), icon: "⚙" },
]);
const skillInsights = computed(() => {
  const assessment = result.value?.assessment || {};
  const toPercent = (score) => Math.max(10, Math.min(100, Number(score || 1) * 20));
  const toTag = (score) => {
    if (score >= 4) return "ADVANCED MASTERY";
    if (score >= 3) return "GROWING";
    return "PRACTICE REQUIRED";
  };
  return [
    {
      key: "grammar",
      label: "Grammar",
      percent: toPercent(assessment.grammar_score),
      tag: toTag(assessment.grammar_score),
    },
    {
      key: "vocabulary",
      label: "Vocabulary",
      percent: toPercent(assessment.vocabulary_score),
      tag: toTag(assessment.vocabulary_score),
    },
    {
      key: "speaking",
      label: "Speaking",
      percent: toPercent(assessment.fluency_score),
      tag: toTag(assessment.fluency_score),
    },
  ];
});
const coachTip = computed(
  () =>
    result.value?.tutor_output?.tutor_message ||
    "Strong progress so far. Keep practicing with complete, confident sentences.",
);
const focusTopic = computed(
  () => result.value?.tutor_output?.focus_topic || "Core Communication",
);
const assessmentScores = computed(() => {
  const assessment = result.value?.assessment || {};
  return {
    grammar: Number(assessment.grammar_score || 1),
    vocabulary: Number(assessment.vocabulary_score || 1),
    fluency: Number(assessment.fluency_score || 1),
  };
});
const accuracyPercent = computed(() => {
  const { grammar, vocabulary, fluency } = assessmentScores.value;
  return Math.round(((grammar + vocabulary + fluency) / 15) * 100);
});
const xpEarned = computed(() => Math.max(15, Math.round(accuracyPercent.value / 2)));
const levelProgressTotal = 1000;
const levelProgressCurrent = computed(() => {
  const base = 620;
  return Math.min(levelProgressTotal, base + xpEarned.value * 5);
});
const levelProgressPercent = computed(() =>
  Math.round((levelProgressCurrent.value / levelProgressTotal) * 100),
);

function navigateTo(path) {
  if (currentPath.value === path) return;
  window.history.pushState({}, "", path);
  currentPath.value = path;
}

function handlePopState() {
  currentPath.value = window.location.pathname || "/";
}

function normalizeRoute() {
  const known = new Set([
    "/",
    "/onboarding/languages",
    "/onboarding/assessment",
    "/dashboard",
  ]);
  if (!known.has(currentPath.value)) {
    navigateTo("/");
    return;
  }

  if (currentPath.value === "/onboarding/assessment" && step.value === 0) {
    step.value = 1;
  }
  if (currentPath.value === "/" || currentPath.value === "/onboarding/languages") {
    if (step.value !== 0) step.value = 0;
  }
}

function saveSession() {
  try {
    localStorage.setItem("vlot_user_id", form.user_id);
    localStorage.setItem("vlot_session_id", form.session_id);
    localStorage.setItem("vlot_display_name", displayName.value);
    localStorage.setItem("vlot_speak_code", selectedSpeakCode.value);
    localStorage.setItem("vlot_learn_code", selectedLearnCode.value);
  } catch {}
}

function loadSession() {
  try {
    const userId = localStorage.getItem("vlot_user_id");
    const sessionId = localStorage.getItem("vlot_session_id");
    const name = localStorage.getItem("vlot_display_name");
    const speakCode = localStorage.getItem("vlot_speak_code");
    const learnCode = localStorage.getItem("vlot_learn_code");
    if (userId) form.user_id = userId;
    if (sessionId) form.session_id = sessionId;
    if (name) displayName.value = name;
    if (speakCode && speakLanguages.some((l) => l.code === speakCode)) selectedSpeakCode.value = speakCode;
    if (learnCode && learnLanguages.some((l) => l.code === learnCode)) selectedLearnCode.value = learnCode;
  } catch {}
}

function clearSession() {
  try {
    [
      "vlot_user_id", "vlot_session_id", "vlot_display_name",
      "vlot_speak_code", "vlot_learn_code", "vlot_zero_start",
      "vlot_unknown_vocab", "vlot_streak",
    ].forEach((k) => localStorage.removeItem(k));
  } catch {}
}

// ── Vocabulary spaced repetition ──────────────────────────────────────────
function getUnknownVocab() {
  try {
    return JSON.parse(localStorage.getItem("vlot_unknown_vocab") || "[]");
  } catch {
    return [];
  }
}

function saveUnknownVocab(items) {
  try {
    const existing = getUnknownVocab();
    const newTerms = items.map((i) => ({ term: i.term, meaning: i.meaning }));
    const merged = [
      ...existing.filter((e) => !newTerms.some((n) => n.term === e.term)),
      ...newTerms,
    ];
    localStorage.setItem("vlot_unknown_vocab", JSON.stringify(merged.slice(-30)));
  } catch {}
}

function removeLearnedVocab(learnedTerms) {
  try {
    const existing = getUnknownVocab();
    localStorage.setItem(
      "vlot_unknown_vocab",
      JSON.stringify(existing.filter((e) => !learnedTerms.includes(e.term))),
    );
  } catch {}
}

// ── Browser notifications ─────────────────────────────────────────────────
async function requestNotificationPermission() {
  if (!("Notification" in window)) return;
  const result = await Notification.requestPermission();
  notificationsPermission.value = result;
  if (result === "granted") {
    localStorage.setItem("vlot_last_practice", Date.now().toString());
  }
}

function updateLastPractice() {
  try {
    const now = Date.now();
    const last = parseInt(localStorage.getItem("vlot_last_practice") || "0", 10);
    const lastDate = last ? new Date(last).toDateString() : null;
    const today = new Date(now).toDateString();
    const yesterday = new Date(now - 86_400_000).toDateString();
    let streak = parseInt(localStorage.getItem("vlot_streak") || "0", 10);
    if (lastDate === today) {
      // already practiced today — keep streak
    } else if (lastDate === yesterday) {
      streak += 1;
    } else {
      streak = 1;
    }
    localStorage.setItem("vlot_last_practice", now.toString());
    localStorage.setItem("vlot_streak", streak.toString());
    currentStreak.value = streak;
  } catch {}
}

function loadStreak() {
  try {
    currentStreak.value = parseInt(localStorage.getItem("vlot_streak") || "0", 10);
  } catch {}
}

function checkPracticeReminder() {
  if (!("Notification" in window) || Notification.permission !== "granted") return;
  try {
    const last = parseInt(localStorage.getItem("vlot_last_practice") || "0", 10);
    if (!last) return;
    const hoursSince = (Date.now() - last) / 3_600_000;
    if (hoursSince >= 24) {
      new Notification("Vlot — Time to practise! 🎓", {
        body: `It's been ${Math.round(hoursSince)} hours since your last session. Keep your streak alive!`,
      });
      updateLastPractice();
    }
  } catch {}
}

// ── Pipeline loading steps ────────────────────────────────────────────────
const pipelineLoadingSteps = [
  "Analysing your answers…",
  "Detecting your language level…",
  "Building your personalised plan…",
  "Designing your lessons…",
  "Almost ready…",
];

async function fetchAiSpeakingFeedback() {
  const answer = lessonResponses.output_speaking.trim();
  if (!answer || answer.length < 10 || isZeroStartMode.value) return;
  aiFeedbackLoading.value = true;
  try {
    const resp = await tutorChat(apiBase.value, {
      user_id: form.user_id,
      session_id: form.session_id,
      user_message: `Give me brief, encouraging feedback (2-3 sentences) on this ${currentLearningLanguage.value} answer: "${answer}"`,
      lesson_id: String(activeLesson.value?.lesson_id || activeLesson.value?.id || ""),
      conversation: tutorConversation.value,
      memory: tutorMemory.value,
      exercise_history: [],
    });
    aiFeedback.value = String(resp.message || "");
    if (Array.isArray(resp.conversation)) tutorConversation.value = resp.conversation;
    if (resp.memory && typeof resp.memory === "object") tutorMemory.value = resp.memory;
  } catch {
    // silently fail — local feedback remains visible
  } finally {
    aiFeedbackLoading.value = false;
  }
}

async function checkGuidedAnswer(idx) {
  const task = guidedExercisePrompts.value[idx];
  const answer = (lessonResponses.guided_practice[idx] || "").trim();
  if (!answer) return;
  guidedCheckLoading.value[idx] = true;
  try {
    const resp = await tutorChat(apiBase.value, {
      user_id: form.user_id || "guest",
      session_id: form.session_id || "local",
      user_message: `Exercise: "${task.prompt}". My answer: "${answer}". Is this correct ${currentLearningLanguage.value}? Give exactly 1 sentence of feedback in English.`,
      conversation: [],
      memory: tutorMemory.value,
      exercise_history: [],
    });
    guidedCheckResults.value[idx] = String(resp.message || resp.tutor_message || "Looks good — keep going!");
  } catch {
    guidedCheckResults.value[idx] = "Could not check right now — continue and review later.";
  } finally {
    guidedCheckLoading.value[idx] = false;
  }
}

async function loadDashboardFromApi() {
  if (!form.user_id || !form.session_id) return;
  try {
    const data = await fetchDashboard(apiBase.value, form.user_id, form.session_id);
    dashboardData.value = data;
    result.value = {
      assessment: data.assessment || {},
      plan: data.plan || {},
      tutor_output: data.tutor_output || {},
    };
    const lessons = Array.isArray(data.lessons) ? data.lessons : [];
    completedWeekNumbers.value = Array.from(
      new Set(
        lessons
          .filter((lesson) => lesson.status === "completed")
          .map((lesson) => Number(lesson.week)),
      ),
    );
    step.value = 5;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
    if (!result.value) navigateTo("/");
  }
}

function selectSpeakLanguage(code) {
  selectedSpeakCode.value = code;
}

function selectLearnLanguage(code) {
  selectedLearnCode.value = code;
}

function startFlow() {
  if (!canStartJourney.value) return;
  result.value = null;
  error.value = "";
  step.value = 1;
  onboardingChoiceModalOpen.value = false;
  navigateTo("/onboarding/assessment");
}

function nextStep() {
  if (!currentAnswer.value.trim()) return;
  if (step.value < 4) {
    step.value += 1;
  } else {
    submitPipeline();
  }
}

function resetFlow() {
  ttsStatus.value = "";
  sessionModalOpen.value = false;
  onboardingChoiceModalOpen.value = false;
  lessonPlayerOpen.value = false;
  activeLessonIndex.value = 0;
  completedWeekNumbers.value = [];
  step.value = 0;
  error.value = "";
  result.value = null;
  dashboardData.value = null;
  isZeroStartMode.value = false;
  displayName.value = "Learner";
  userName.value = "";
  aiFeedback.value = "";
  tutorConversation.value = [];
  tutorMemory.value = {};
  form.user_id = "demo-user";
  form.session_id = "session-1";
  form.answer1 = "";
  form.answer2 = "";
  form.answer3 = "";
  form.answer4 = "";
  clearSession();
  navigateTo("/");
}

function noop() {}

function openLanguagePicker() {
  navigateTo("/onboarding/languages");
  step.value = 0;
}

function openOnboardingChoiceModal() {
  if (!canStartJourney.value) return;
  onboardingChoiceModalOpen.value = true;
}

function closeOnboardingChoiceModal() {
  onboardingChoiceModalOpen.value = false;
}

function buildZeroStartResult() {
  const target = currentLearningLanguage.value;
  const weeklyGoals = Array.from({ length: 12 }, (_, index) => {
    const week = index + 1;
    return {
      week,
      focus:
        week <= 4
          ? `Foundation week ${week}: core ${target} basics`
          : week <= 8
            ? `Development week ${week}: grammar and communication`
            : `Fluency week ${week}: speaking confidence and review`,
      exercises: [
        "Short speaking drill aligned with the weekly focus",
        "Sentence building with self-correction",
      ],
    };
  });
  return {
    assessment: {
      level: "A1",
      reasoning: `User chooses a complete beginner path for ${target}.`,
      vocabulary_score: 1,
      grammar_score: 1,
      fluency_score: 1,
      weak_areas: [
        "basic greetings",
        "introductions",
        "very simple sentence building",
      ],
      strong_areas: ["learning motivation"],
      recommended_focus: `Start from zero with core ${target} survival phrases and sentence basics.`,
    },
    plan: {
      level: "A1",
      target_level: "A2",
      duration_weeks: 12,
      weekly_goals: weeklyGoals,
      priority_skills: ["vocabulary", "grammar", "speaking confidence"],
      summary: `Begin from zero and build a practical ${target} foundation in 3 months.`,
    },
    tutor_output: {
      tutor_message: `Great choice. We'll start from zero in ${target} with short and practical steps.`,
      suggested_exercise:
        "Learn 8 core greeting phrases and use each one in a simple dialogue.",
      focus_topic: "Beginner foundations",
      difficulty_adjustment: "easier",
      lesson_outline: lessonTemplatePhases,
      memory_note: "User starts from zero and prefers structured beginner steps.",
    },
  };
}

const isZeroStartMode = ref(false);

function startFromZero() {
  const zeroResult = buildZeroStartResult();
  result.value = zeroResult;
  if (userName.value.trim()) displayName.value = userName.value.trim();
  completedWeekNumbers.value = [];
  step.value = 5;
  isZeroStartMode.value = true;
  dashboardData.value = null;
  onboardingChoiceModalOpen.value = false;
  try {
    localStorage.setItem("vlot_zero_start", JSON.stringify({
      result: zeroResult,
      displayName: displayName.value,
      speakCode: selectedSpeakCode.value,
      learnCode: selectedLearnCode.value,
    }));
  } catch {}
  navigateTo("/dashboard");
}

function resetLessonInputs() {
  lessonResponses.warm_up = ["", "", ""];
  lessonResponses.input_vocab_checks = inputVocabularyItems.value.map(() => false);
  lessonResponses.input_check = "";
  lessonResponses.guided_practice = guidedExercisePrompts.value.map(() => "");
  lessonResponses.output_speaking = "";
  lessonResponses.feedback_reflection = "";
  outputFollowUpQuestion.value = "";
  outputFollowUpAnswer.value = "";
  outputUsedSpeech.value = false;
  outputFollowUpUsedSpeech.value = false;
  phaseValidationError.value = "";
  aiFeedback.value = "";
  guidedHintsVisible.value = guidedExercisePrompts.value.map(() => false);
  guidedCheckResults.value = guidedExercisePrompts.value.map(() => "");
  guidedCheckLoading.value = guidedExercisePrompts.value.map(() => false);
}

function requestOutputFollowUpQuestion() {
  phaseValidationError.value = "";
  const baseAnswer = lessonResponses.output_speaking.trim();
  if (baseAnswer.length < 20) {
    phaseValidationError.value = t("followupNeedBase");
    return;
  }
  const topic =
    activeLesson.value?.title || activeLesson.value?.focus || currentLessonPhase.value?.goal || "today's topic";
  const words = speakingFocusWords.value.slice(0, 2);
  const wordPart = words.length
    ? ` Try to include "${words.join('" and "')}" in your answer.`
    : "";
  outputFollowUpQuestion.value = `Follow-up challenge: Tell me one more practical sentence about ${topic}.${wordPart}`;
  if (settingsTtsEnabled.value) {
    speakText(outputFollowUpQuestion.value, ttsLangCode.value);
  }
  aiFeedback.value = "";
  fetchAiSpeakingFeedback();
}

function handleOutputSpeechResult(transcript) {
  const text = String(transcript || "").trim();
  if (!text) return;
  outputUsedSpeech.value = true;
  lessonResponses.output_speaking += (lessonResponses.output_speaking ? " " : "") + text;
}

function handleOutputFollowUpSpeechResult(transcript) {
  const text = String(transcript || "").trim();
  if (!text) return;
  outputFollowUpUsedSpeech.value = true;
  outputFollowUpAnswer.value += (outputFollowUpAnswer.value ? " " : "") + text;
}

function validatePhaseInputs(phaseName) {
  phaseValidationError.value = "";
  if (phaseName === "warm_up") {
    const answered = lessonResponses.warm_up.filter((x) => x.trim().length >= 6).length;
    if (answered < 2) {
      phaseValidationError.value = t("warmupValidation");
      return false;
    }
  } else if (phaseName === "input") {
    const threshold = Math.min(5, inputVocabularyItems.value.length || 0);
    if (knownWordCount.value < threshold) {
      phaseValidationError.value = t("inputVocabValidation", { n: threshold });
      return false;
    }
    if (lessonResponses.input_check.trim().length < 8) {
      phaseValidationError.value = t("inputCheckValidation");
      return false;
    }
  } else if (phaseName === "guided_practice") {
    const allDone = lessonResponses.guided_practice.every((x) => x.trim().length >= 2);
    if (!allDone) {
      phaseValidationError.value = t("guidedValidation");
      return false;
    }
  } else if (phaseName === "output_speaking") {
    if (lessonResponses.output_speaking.trim().length < 20) {
      phaseValidationError.value = t("outputMinValidation");
      return false;
    }
    if (!outputFollowUpQuestion.value.trim()) {
      phaseValidationError.value = t("outputNeedFollowQuestion");
      return false;
    }
    if (outputFollowUpAnswer.value.trim().length < 12) {
      phaseValidationError.value = t("outputNeedFollowAnswer");
      return false;
    }
  } else if (phaseName === "feedback_correction") {
    if (lessonResponses.feedback_reflection.trim().length < 8) {
      phaseValidationError.value = t("feedbackValidation");
      return false;
    }
  }
  return true;
}

async function openLesson(lesson) {
  if (lesson.locked) return;
  error.value = "";

  // Zero-start mode: no backend data, open lesson player directly
  if (isZeroStartMode.value) {
    activeLessonIndex.value = lesson.index;
    activePhaseIndex.value = 0;
    resetLessonInputs();
    phaseStartTime.value = Date.now();
    lessonPlayerOpen.value = true;
    return;
  }

  lessonNetworkBusy.value = true;
  try {
    const startPayload = await startLesson(
      apiBase.value,
      form.user_id,
      form.session_id,
      Number(lesson.week || 1),
      String(lesson.lesson_id || lesson.id),
    );
    if (startPayload.status === "locked") return;
    activeLessonIndex.value = lesson.index;
    const lastPhase = Number(startPayload.last_phase || 0);
    activePhaseIndex.value = Math.max(0, Math.min(4, lastPhase));
    resetLessonInputs();
    phaseStartTime.value = Date.now();
    lessonPlayerOpen.value = true;
    updateLastPractice();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    lessonNetworkBusy.value = false;
  }
}

function closeLessonPlayer() {
  lessonPlayerOpen.value = false;
  activePhaseIndex.value = 0;
  phaseValidationError.value = "";
}

async function nextLessonPhase() {
  const lesson = activeLesson.value;
  const phase = currentLessonPhase.value;
  if (!lesson || !phase) return;
  if (!validatePhaseInputs(String(phase.phase))) return;
  error.value = "";

  // Zero-start mode: advance phases locally without API calls
  if (isZeroStartMode.value) {
    if (activePhaseIndex.value < effectiveLessonOutline.value.length - 1) {
      activePhaseIndex.value += 1;
    } else {
      await completeLesson();
    }
    return;
  }

  lessonNetworkBusy.value = true;
  try {
    let phasePayload = {};
    if (phase.phase === "warm_up") {
      phasePayload = { answers: [...lessonResponses.warm_up], questions: [...warmupQuestions.value] };
    } else if (phase.phase === "input") {
      const learnedItems = inputVocabularyItems.value.filter(
        (_, idx) => Boolean(lessonResponses.input_vocab_checks[idx]),
      );
      const unknownItems = inputVocabularyItems.value.filter(
        (_, idx) => !lessonResponses.input_vocab_checks[idx],
      );
      saveUnknownVocab(unknownItems);
      removeLearnedVocab(learnedItems.map((i) => i.term));
      phasePayload = {
        check_answer: lessonResponses.input_check,
        vocab_terms: inputVocabularyItems.value.map((item) => item.term),
        learned_terms: learnedItems.map((item) => item.term),
      };
    } else if (phase.phase === "guided_practice") {
      phasePayload = {
        prompts: guidedExercisePrompts.value.map((task) => task.prompt),
        answers: [...lessonResponses.guided_practice],
      };
    } else if (phase.phase === "output_speaking") {
      phasePayload = {
        scenario: outputScenario.value,
        learner_response: lessonResponses.output_speaking,
        first_feedback: outputPrimaryFeedback.value,
        follow_up_question: outputFollowUpQuestion.value,
        follow_up_response: outputFollowUpAnswer.value,
        follow_up_feedback: outputFollowUpFeedback.value,
        used_speech_input: outputUsedSpeech.value,
        used_speech_follow_up: outputFollowUpUsedSpeech.value,
      };
    } else if (phase.phase === "feedback_correction") {
      phasePayload = { reflection: lessonResponses.feedback_reflection };
    }
    await submitLessonPhase(apiBase.value, {
      user_id: form.user_id,
      session_id: form.session_id,
      week: Number(lesson.week),
      lesson_id: String(lesson.lesson_id || lesson.id),
      phase: String(phase.phase),
      payload: phasePayload,
      score: Math.max(60, accuracyPercent.value - 5),
      hints_used: 0,
      retries: 0,
      duration_seconds: Math.round((Date.now() - phaseStartTime.value) / 1000),
    });
    if (activePhaseIndex.value < lessonOutlineForSession.value.length - 1) {
      activePhaseIndex.value += 1;
      return;
    }
    await completeLesson();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
    retryFn.value = nextLessonPhase;
  } finally {
    lessonNetworkBusy.value = false;
  }
}

function previousLessonPhase() {
  if (activePhaseIndex.value > 0) {
    activePhaseIndex.value -= 1;
  }
}

async function completeLesson() {
  const lesson = activeLesson.value;
  if (!lesson) return;

  if (!isZeroStartMode.value) {
    await completeLessonApi(apiBase.value, {
      user_id: form.user_id,
      session_id: form.session_id,
      week: Number(lesson.week),
      lesson_id: String(lesson.lesson_id || lesson.id),
      accuracy: accuracyPercent.value,
      xp_earned: xpEarned.value,
      weak_topics: assessmentWeakAreas.value,
    });
    await loadDashboardFromApi();
  }

  if (!completedWeekNumbers.value.includes(Number(lesson.week))) {
    completedWeekNumbers.value = [...completedWeekNumbers.value, Number(lesson.week)];
  }
  lessonPlayerOpen.value = false;
  openSessionCompleteModal();
}

function openSessionCompleteModal() {
  sessionModalOpen.value = true;
}

function closeSessionCompleteModal() {
  sessionModalOpen.value = false;
}

function playTutorTts() {
  const msg = result.value?.tutor_output?.tutor_message;
  if (msg) speakText(msg, ttsLangCode.value);
}

function speakText(text, langCode) {
  if (!settingsTtsEnabled.value) return;
  if (!("speechSynthesis" in window)) {
    error.value = "Text-to-speech is not supported in this browser.";
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = langCode || ttsLangCode.value;
  utterance.rate = Math.max(0.5, Math.min(2, settingsPlaybackRate.value / 150));
  utterance.volume = 1.0;
  let voice = null;
  if (selectedVoiceURI.value) {
    voice = availableVoices.value.find((v) => v.voiceURI === selectedVoiceURI.value) || null;
  }
  if (!voice) {
    voice = pickBestVoiceForLang(utterance.lang);
    if (voice) selectedVoiceURI.value = voice.voiceURI;
  }
  if (voice) utterance.voice = voice;
  window.speechSynthesis.speak(utterance);
}

// onResult: called with the transcript string — defaults to appending to output_speaking
function startStt(onResult) {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    error.value = "Speech recognition is not supported in this browser. Try Chrome or Edge.";
    return;
  }
  if (sttActive.value) {
    sttRecognizer?.stop();
    sttActive.value = false;
    return;
  }
  const defaultHandler = (text) => {
    lessonResponses.output_speaking += (lessonResponses.output_speaking ? " " : "") + text;
  };
  const handler = typeof onResult === "function" ? onResult : defaultHandler;
  sttRecognizer = new SpeechRec();
  sttRecognizer.lang = ttsLangCode.value;
  sttRecognizer.continuous = false;
  sttRecognizer.interimResults = false;
  sttActive.value = true;
  sttRecognizer.onresult = (event) => {
    const results = Array.from(event.results);
    const transcript = results.map((r) => r[0].transcript).join(" ");
    const totalConf = results.reduce((sum, r) => sum + (r[0].confidence || 0), 0);
    sttConfidence.value = results.length
      ? Math.round((totalConf / results.length) * 100)
      : 0;
    handler(transcript);
  };
  sttRecognizer.onend = () => { sttActive.value = false; };
  sttRecognizer.onerror = () => { sttActive.value = false; };
  sttRecognizer.start();
}

async function submitPipeline() {
  loading.value = true;
  pipelineLoadingStep.value = 0;
  error.value = "";
  result.value = null;
  step.value = 6;
  const stepTimer = setInterval(() => {
    if (pipelineLoadingStep.value < pipelineLoadingSteps.length - 1) {
      pipelineLoadingStep.value += 1;
    }
  }, 4000);
  try {
    // Get a real user_id + session_id from the backend
    const loginResp = await guestLogin(
      apiBase.value,
      userName.value.trim() || "Learner",
    );
    form.user_id = String(loginResp.user_id || form.user_id);
    form.session_id = String(loginResp.session_id || form.session_id);
    displayName.value = String(loginResp.display_name || userName.value || "Learner");

    const pipelineData = await runPipeline(apiBase.value, {
        ...form,
        user_input:
        `I already speak ${currentSpeakingLanguage.value} and I want to learn ${currentLearningLanguage.value}. I have finished the 4 questions. Please give me my first personalized tutoring step.`,
        speak_language: currentSpeakingLanguage.value,
        learn_language: currentLearningLanguage.value,
        lessons_per_week: lessonsPerWeek.value,
    });
    result.value = pipelineData;
    completedWeekNumbers.value = [];
    saveSession();
    await loadDashboardFromApi();
    step.value = 5;
    navigateTo("/dashboard");
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
    retryFn.value = submitPipeline;
    step.value = 4;
  } finally {
    clearInterval(stepTimer);
    loading.value = false;
  }
}

function loadVoices() {
  const voices = window.speechSynthesis?.getVoices() || [];
  availableVoices.value = voices;
  const stillAvailable = voices.some((v) => v.voiceURI === selectedVoiceURI.value);
  if (stillAvailable) return;
  const preferred = pickBestVoiceForLang(ttsLangCode.value);
  if (preferred) selectedVoiceURI.value = preferred.voiceURI;
}

function scoreVoiceForQuality(voice) {
  const n = `${voice.name || ""} ${voice.voiceURI || ""}`.toLowerCase();
  let score = 0;
  if (voice.localService) score += 4;
  if (n.includes("siri")) score += 14;
  if (n.includes("google")) score += 12;
  if (n.includes("microsoft")) score += 10;
  if (n.includes("neural")) score += 12;
  if (n.includes("natural")) score += 8;
  if (n.includes("enhanced")) score += 8;
  if (n.includes("premium")) score += 8;
  if (n.includes("high quality")) score += 8;
  if (n.includes("compact")) score -= 6;
  if (n.includes("novelty")) score -= 8;
  if (n.includes("whisper")) score -= 3;
  return score;
}

function pickBestVoiceForLang(langCode) {
  const voices = availableVoices.value || [];
  if (!voices.length) return null;
  const exact = voices.filter((v) => v.lang === langCode);
  const prefix = String(langCode || "en-US").split("-")[0];
  const byPrefix = voices.filter((v) => v.lang.startsWith(prefix));
  const candidates = exact.length ? exact : byPrefix.length ? byPrefix : voices;
  if (!candidates.length) return null;
  const hints = ttsDefaultVoiceHintsByLang[prefix] || [];
  const withPreference = [...candidates].sort((a, b) => {
    const aName = `${a.name || ""} ${a.voiceURI || ""}`.toLowerCase();
    const bName = `${b.name || ""} ${b.voiceURI || ""}`.toLowerCase();
    const aPref = hints.some((hint) => aName.includes(hint)) ? 1 : 0;
    const bPref = hints.some((hint) => bName.includes(hint)) ? 1 : 0;
    if (aPref !== bPref) return bPref - aPref;
    return scoreVoiceForQuality(b) - scoreVoiceForQuality(a);
  });
  return withPreference[0] || null;
}

onMounted(() => {
  window.addEventListener("popstate", handlePopState);

  // Restore zero-start session from localStorage
  try {
    const saved = localStorage.getItem("vlot_zero_start");
    if (saved) {
      const parsed = JSON.parse(saved);
      result.value = parsed.result;
      displayName.value = parsed.displayName || "Learner";
      if (parsed.speakCode) selectedSpeakCode.value = parsed.speakCode;
      if (parsed.learnCode) selectedLearnCode.value = parsed.learnCode;
      isZeroStartMode.value = true;
      step.value = 5;
      if (currentPath.value !== "/dashboard") navigateTo("/dashboard");
    } else {
      loadSession();
    }
  } catch {
    loadSession();
  }

  checkPracticeReminder();
  loadStreak();
  normalizeRoute();
  if (currentPath.value === "/dashboard" && !isZeroStartMode.value) {
    loadDashboardFromApi();
  }
  if ("speechSynthesis" in window) {
    loadVoices();
    window.speechSynthesis.addEventListener("voiceschanged", loadVoices);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("popstate", handlePopState);
  window.speechSynthesis?.removeEventListener("voiceschanged", loadVoices);
});

watch(ttsLangCode, () => {
  const preferred = pickBestVoiceForLang(ttsLangCode.value);
  selectedVoiceURI.value = preferred ? preferred.voiceURI : "";
});

watch(currentPath, () => {
  normalizeRoute();
  if (currentPath.value === "/dashboard" && !result.value) {
    loadDashboardFromApi();
  }
});

watch(activePhaseIndex, () => {
  phaseStartTime.value = Date.now();
});
</script>

<template>
  <main class="app-shell">
    <header v-if="!showDashboard" class="top-nav">
      <div class="brand">Vlot</div>
      <nav class="nav-links">
        <a href="/" @click.prevent="navigateTo('/')">{{ t("navHowItWorks") }}</a>
        <a href="/" @click.prevent="navigateTo('/')">{{ t("navFeatures") }}</a>
        <a href="/" @click.prevent="navigateTo('/')">{{ t("navPricing") }}</a>
      </nav>
      <div class="nav-actions">
        <button class="link-button">{{ t("navSignIn") }}</button>
        <button class="small-cta" @click="openLanguagePicker">{{ t("navGetStarted") }}</button>
    </div>
    </header>

    <section v-if="showLanding" class="marketing-page">
      <section class="marketing-hero">
        <div class="hero-copy">
          <h1>
            {{ t("heroHeadingPrefix") }} <span>{{ t("heroHeadingHighlight") }}</span> {{ t("heroHeadingSuffix") }}
          </h1>
          <p>
            AI-powered coaching that adapts to your goals with precision and practical daily sessions.
          </p>
          <div class="hero-actions">
            <button @click="openLanguagePicker">{{ t("navGetStarted") }}</button>
            <button class="secondary" @click="noop">{{ t("seeHowItWorks") }}</button>
          </div>
        </div>
        <div class="hero-media">
          <div class="hero-image">🎓</div>
          <div class="hero-chip">
            <strong>{{ t("heroProgressTitle") }}</strong>
            <span>{{ t("heroProgressSubtitle") }}</span>
          </div>
        </div>
      </section>

      <section class="elegance-section">
        <h2>{{ t("eleganceTitle") }}</h2>
        <p>
          A refined learning experience designed for meaningful progress and measurable growth.
        </p>
        <div class="feature-grid">
          <article v-for="feature in landingFeatures" :key="feature.title" class="feature-card">
            <div class="feature-icon">◆</div>
            <h3>{{ feature.title }}</h3>
            <p>{{ feature.description }}</p>
          </article>
        </div>
      </section>

      <section class="journey-section">
        <h2>
          {{ t("journeyTitlePrefix") }} <span>{{ t("journeyTitleHighlight") }}</span>
        </h2>
        <div class="journey-list">
          <article
            v-for="(item, index) in landingJourney"
            :key="item.title"
            class="journey-item"
          >
            <div class="journey-index">0{{ index + 1 }}</div>
            <div class="journey-content">
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </div>
            <div class="journey-visual">{{ item.visual }}</div>
          </article>
        </div>
      </section>

      <section class="rewards-section">
        <div class="reward-progress card-lite">
          <h3>{{ t("quietPersistence") }}</h3>
          <p>{{ t("streakDays") }}</p>
          <div class="skill-track">
            <div class="skill-fill" style="width: 85%"></div>
          </div>
          <small>{{ t("nextMilestone") }}</small>
        </div>
        <div class="reward-copy">
          <h3>{{ t("quietRewards") }}</h3>
          <p>
            Keep momentum with daily streaks, XP milestones, and confidence markers that reveal steady growth.
          </p>
        </div>
      </section>

      <section class="final-cta">
        <h2>
          {{ t("finalCtaPrefix") }} <span>{{ t("finalCtaHighlight") }}</span> {{ t("finalCtaSuffix") }}
        </h2>
        <p>
          A clear pathway of assessment, planning, and guided practice crafted to help you improve every week.
        </p>
        <div class="hero-actions">
          <button @click="openLanguagePicker">{{ t("heroGetStartedNow") }}</button>
          <button class="secondary" @click="noop">{{ t("scheduleDemo") }}</button>
        </div>
      </section>
    </section>

    <section v-else-if="showLanguagePicker" class="language-page">
      <h1>
        Your journey to mastery <br />
        <span>{{ t("languageFocusTagline") }}</span>
      </h1>
      <p class="subtitle">
        Tailor your language path by selecting what you already speak and what you want to learn next.
      </p>

      <div class="language-section">
        <div class="section-label">{{ t("alreadySpeak") }}</div>
        <div class="language-grid">
          <button
            v-for="language in speakLanguages"
            :key="`speak-${language.code}`"
            class="language-card"
            :class="{ selected: selectedSpeakCode === language.code }"
            @click="selectSpeakLanguage(language.code)"
          >
            <span class="flag">{{ language.emoji }}</span>
            <span>{{ language.label }}</span>
            <span
              v-if="selectedSpeakCode === language.code"
              class="checkmark"
              aria-hidden="true"
              >✓</span
            >
          </button>
        </div>
      </div>

      <div class="language-section">
        <div class="section-label">{{ t("wantLearn") }}</div>
        <div class="language-grid">
          <button
            v-for="language in learnLanguages"
            :key="`learn-${language.code}`"
            class="language-card"
            :class="{ selected: selectedLearnCode === language.code }"
            @click="selectLearnLanguage(language.code)"
          >
            <span class="flag">{{ language.emoji }}</span>
            <span>{{ language.label }}</span>
            <span
              v-if="selectedLearnCode === language.code"
              class="checkmark"
              aria-hidden="true"
              >✓</span
            >
          </button>
        </div>
      </div>

      <button class="primary-cta" :disabled="!canStartJourney" @click="openOnboardingChoiceModal">
        {{ t("continueJourney") }}
      </button>
      <p class="helper-text">
        {{ t("helperText") }}
      </p>

      <div
        v-if="onboardingChoiceModalOpen"
        class="onboarding-choice-overlay"
        role="dialog"
        aria-modal="true"
        aria-label="Choose onboarding mode"
      >
        <div class="onboarding-choice-modal">
          <h3>{{ t("onboardingTitle") }}</h3>
          <p>
            {{ t("onboardingDesc") }}
          </p>
          <div class="onboarding-name-row">
            <label class="onboarding-name-label">Your name (optional)</label>
            <input
              v-model="userName"
              class="onboarding-name-input"
              placeholder="e.g. Sofia"
              maxlength="40"
            />
          </div>
          <div class="onboarding-lpw-row">
            <label class="onboarding-name-label">Lessons per week</label>
            <div class="lpw-options">
              <button
                v-for="n in [2, 3]"
                :key="n"
                class="lpw-btn"
                :class="{ selected: lessonsPerWeek === n }"
                @click="lessonsPerWeek = n"
              >{{ n }}×</button>
            </div>
          </div>
          <div class="onboarding-choice-actions">
            <button @click="startFromZero">{{ t("startZero") }}</button>
            <button class="secondary" @click="startFlow">
              {{ t("doAssessment") }}
            </button>
          </div>
          <button class="onboarding-close" @click="closeOnboardingChoiceModal">{{ t("cancel") }}</button>
        </div>
      </div>
    </section>

    <section
      v-else-if="showAssessmentRoute || showDashboard"
      :class="['workflow', { 'workflow-dashboard': showDashboard }]"
    >
      <div v-if="!inAssessment && !showDashboard" class="header">
        <h2>{{ t("appTitle") }}</h2>
      </div>

      <section v-if="!inAssessment && !showDashboard" class="card settings">
      <div class="grid">
        <div>
            <label>{{ t("apiBaseUrl") }}</label>
          <input v-model="apiBase" placeholder="http://localhost:8000" />
        </div>
        <div>
            <label>{{ t("userId") }}</label>
          <input v-model="form.user_id" />
        </div>
        <div>
            <label>{{ t("sessionId") }}</label>
          <input v-model="form.session_id" />
        </div>
      </div>
    </section>

      <section v-if="inAssessment" class="assessment-shell">
        <div class="assessment-meta">
          <span class="assessment-step">{{ t("assessmentStep") }} {{ step }} {{ t("of") }} {{ totalAssessmentSteps }}</span>
          <span class="assessment-percent">{{ assessmentProgress }}% {{ t("complete") }}</span>
        </div>
        <div class="assessment-progress">
          <div class="assessment-progress-fill" :style="{ width: `${assessmentProgress}%` }"></div>
        </div>

        <div class="assessment-chat">
          <article
            v-for="(message, index) in assessmentMessages"
            :key="`message-${index}`"
            class="chat-row"
            :class="{ 'is-user': message.role === 'user' }"
          >
            <div v-if="message.role === 'coach'" class="avatar ai-avatar">AI</div>
            <div class="chat-bubble" :class="message.role === 'user' ? 'user-bubble' : 'coach-bubble'">
              {{ message.text }}
            </div>
            <div v-if="message.role === 'user'" class="avatar user-avatar">{{ t("youLabel") }}</div>
          </article>
          <p class="chat-meta">{{ assessmentMessages.at(-1)?.meta || "VLOT AI" }}</p>
        </div>

        <div class="assessment-composer">
          <input
        v-model="currentAnswer"
            :placeholder="responsePlaceholder"
            @keyup.enter="nextStep"
          />
          <button
            class="send-btn"
            :disabled="!currentAnswer.trim() || loading"
            @click="nextStep"
          >
            ->
        </button>
          <button
            class="mic-btn assessment-mic"
            :class="{ active: sttActive }"
            type="button"
            :title="sttActive ? 'Listening… click to stop' : 'Speak your answer'"
            @click="startStt((t) => { const key = answerKeys[step - 1]; if (key) form[key] += (form[key] ? ' ' : '') + t; })"
          >{{ sttActive ? '🔴' : '🎤' }}</button>
      </div>
        <p class="assessment-tip">
          {{ t("assessmentTip") }} {{ currentSpeakingLanguage }}, {{ t("answerIn") }} {{ currentLearningLanguage }}.
        </p>
    </section>

    <section v-else-if="step === 6" class="card loading-card">
      <div class="spinner" aria-hidden="true"></div>
      <h2>{{ t("loadingPlan") }}</h2>
      <ol class="pipeline-steps">
        <li
          v-for="(label, i) in pipelineLoadingSteps"
          :key="i"
          class="pipeline-step"
          :class="{
            'step-done':   i < pipelineLoadingStep,
            'step-active': i === pipelineLoadingStep,
            'step-pending': i > pipelineLoadingStep,
          }"
        >
          <span class="step-icon">
            {{ i < pipelineLoadingStep ? '✓' : i === pipelineLoadingStep ? '⟳' : '○' }}
          </span>
          {{ label }}
        </li>
      </ol>
    </section>

      <section v-else-if="showDashboard && result && step !== 6" class="dashboard-layout">
        <aside class="dashboard-sidebar">
          <div class="sidebar-brand">Vlot</div>
          <div class="learner-card">
            <div class="learner-avatar">👩‍🎓</div>
            <div>
              <strong>{{ t("risingLearner") }}</strong>
              <p>{{ t("level4") }}</p>
            </div>
          </div>
          <nav class="sidebar-nav">
            <button
              v-for="item in progressNavItems"
              :key="item.key"
              class="nav-item"
              :class="{ active: dashboardTab === item.key }"
              @click="dashboardTab = item.key"
            >
              <span class="nav-icon">{{ item.icon }}</span>
              <span>{{ item.label }}</span>
            </button>
          </nav>
          <button class="upgrade-btn" @click="resetFlow">{{ t("startOver") }}</button>
        </aside>

        <div class="dashboard-main">
          <header class="dashboard-header">
            <div>
              <h1>{{ t("welcomeBack") }} {{ displayName || "Learner" }} 👋</h1>
              <p>{{ t("readyDaily") }}</p>
      </div>
            <div class="dashboard-header-badges">
              <span class="streak-badge">🔥 {{ t("streakBadge") }}</span>
              <span class="level-badge">{{ learnerLevelLabel }}</span>
            </div>
          </header>

          <div v-if="dashboardTab === 'home'" class="dashboard-grid">
            <section class="weekly-plan card-lite">
              <div class="weekly-plan-header">
                <h2>{{ t("plan12w") }}</h2>
                <button class="link-button" @click="dashboardTab = 'plan'">{{ t("viewCalendar") }}</button>
      </div>

              <article
                v-for="(lesson, index) in weeklyLessons"
                :key="lesson.id"
                class="lesson-item"
                :class="{ done: lesson.completed }"
              >
                <div class="lesson-icon">{{ index === 0 ? "💬" : index === 1 ? "📖" : "🍽" }}</div>
                <div class="lesson-content">
                  <p class="day-label">{{ lesson.dayLabel }}</p>
                  <h3>{{ lesson.title }}</h3>
                  <p class="lesson-meta">● {{ lesson.minutes }} min &nbsp;&nbsp; ✦ +{{ lesson.xp }} XP</p>
                </div>
                <button
                  class="lesson-action"
                  :class="{ locked: lesson.locked }"
                  :disabled="lesson.locked || lessonNetworkBusy"
                  @click="openLesson(lesson)"
                >
                  {{ lesson.locked ? t("locked") : lesson.completed ? t("completed") : t("start") }}
                </button>
              </article>
            </section>

            <aside class="dashboard-right">
              <section class="card-lite skill-card">
                <h3>{{ t("skillInsightsTitle") }}</h3>
                <div v-for="skill in skillInsights" :key="skill.key" class="skill-row">
                  <div class="skill-head">
                    <span>{{ skill.label }}</span>
                    <small>{{ skill.tag }}</small>
                  </div>
                  <div class="skill-track">
                    <div class="skill-fill" :style="{ width: `${skill.percent}%` }"></div>
                  </div>
                </div>
              </section>

              <section class="card-lite tip-card">
                <h4>{{ t("coachTipTitle") }}</h4>
                <p>"{{ coachTip }}"</p>
                <div class="tip-actions">
        <button class="secondary" :disabled="ttsLoading" @click="playTutorTts">
                    {{ ttsLoading ? t("speakingLoading") : t("readAloud") }}
        </button>
                  <button @click="resetFlow">{{ t("startOver") }}</button>
      </div>
      <p v-if="ttsStatus" class="tts-status">{{ ttsStatus }}</p>
              </section>

              <section class="card-lite achievement-card">
                <h4>{{ t("recentAchievement") }}</h4>
                <strong>{{ focusTopic }}</strong>
                <p>{{ result?.tutor_output?.suggested_exercise }}</p>
              </section>
              <section v-if="dashboardMetrics" class="card-lite achievement-card">
                <h4>{{ t("learningMetrics") }}</h4>
                <p>Completion: {{ dashboardMetrics.completion_rate }}%</p>
                <p>Avg accuracy: {{ dashboardMetrics.avg_accuracy }}%</p>
                <p>Total XP: {{ dashboardMetrics.total_xp }}</p>
              </section>
              <section class="card-lite achievement-card">
                <h4>{{ t("reviewDueTodayTitle") }}</h4>
                <p v-if="!reviewDueToday.length">{{ t("noDueReviews") }}</p>
                <template v-else>
                  <ul class="review-due-list">
                    <li v-for="item in reviewDueToday" :key="item.id">
                      {{ item.topic }} (from week {{ item.source_week }})
                    </li>
                  </ul>
                  <button
                    class="small-cta"
                    style="margin-top:10px;width:100%"
                    @click="reviewSessionOpen = true; activeReviewIndex = 0"
                  >Start review session ({{ reviewDueToday.length }} topics)</button>
                </template>
              </section>
            </aside>
          </div>

          <!-- Plan tab -->
          <div v-else-if="dashboardTab === 'plan'" class="dashboard-tab-panel">
            <h2 class="tab-panel-title">{{ t("planTabTitle") }}</h2>
            <div class="plan-meta-row">
              <div class="plan-meta-card">
                <small>{{ t("currentLevel") }}</small>
                <strong>{{ result?.assessment?.level || '—' }}</strong>
              </div>
              <div class="plan-meta-card">
                <small>{{ t("targetLevel") }}</small>
                <strong>{{ result?.plan?.target_level || '—' }}</strong>
              </div>
              <div class="plan-meta-card">
                <small>{{ t("duration") }}</small>
                <strong>{{ result?.plan?.duration_weeks || 12 }} weeks</strong>
              </div>
              <div class="plan-meta-card">
                <small>{{ t("lessonsDone") }}</small>
                <strong>{{ completedLessonsCount }} / {{ curriculumLessons.length }}</strong>
              </div>
            </div>
            <div class="plan-goals-list">
              <div
                v-for="goal in (result?.plan?.weekly_goals || [])"
                :key="goal.week"
                class="plan-goal-row"
                :class="{ 'is-done': completedLessonsCount >= goal.week }"
              >
                <div class="plan-goal-week">W{{ goal.week }}</div>
                <div class="plan-goal-body">
                  <strong>{{ goal.focus }}</strong>
                  <p v-if="goal.grammar_focus">Grammar: {{ goal.grammar_focus }}</p>
                  <p v-if="Array.isArray(goal.vocabulary_targets) && goal.vocabulary_targets.length">
                    Vocab: {{ goal.vocabulary_targets.slice(0, 5).join(', ') }}{{ goal.vocabulary_targets.length > 5 ? '…' : '' }}
                  </p>
                </div>
                <span v-if="completedLessonsCount >= goal.week" class="plan-goal-check">✓</span>
              </div>
            </div>
            <p v-if="result?.plan?.overall_summary" class="plan-summary-note">
              {{ result.plan.overall_summary }}
            </p>
          </div>

          <!-- Progress tab -->
          <div v-else-if="dashboardTab === 'progress'" class="dashboard-tab-panel">
            <h2 class="tab-panel-title">{{ t("progressTabTitle") }}</h2>
            <div class="plan-meta-row">
              <div class="plan-meta-card">
                <small>{{ t("totalXp") }}</small>
                <strong>{{ totalXpEarned }} XP</strong>
              </div>
              <div class="plan-meta-card">
                <small>{{ t("lessonsDone") }}</small>
                <strong>{{ completedLessonsCount }}</strong>
              </div>
              <div class="plan-meta-card">
                <small>{{ t("avgAccuracy") }}</small>
                <strong>{{ dashboardMetrics ? dashboardMetrics.avg_accuracy + '%' : accuracyPercent + '%' }}</strong>
              </div>
              <div class="plan-meta-card">
                <small>{{ t("reviewsDue") }}</small>
                <strong>{{ reviewDueToday.length }}</strong>
              </div>
              <div v-if="dashboardMetrics?.total_minutes_practiced" class="plan-meta-card">
                <small>Time practiced</small>
                <strong>{{ dashboardMetrics.total_minutes_practiced }} min</strong>
              </div>
            </div>
            <div v-if="dashboardMetrics?.phase_scores && Object.keys(dashboardMetrics.phase_scores).length" class="phase-scores-section">
              <h3 class="progress-section-title">Phase accuracy</h3>
              <div class="phase-scores-grid">
                <div
                  v-for="(score, phase) in dashboardMetrics.phase_scores"
                  :key="phase"
                  class="phase-score-card"
                >
                  <small>{{ String(phase).replaceAll('_', ' ') }}</small>
                  <strong>{{ score }}%</strong>
                  <div class="phase-score-bar">
                    <div class="phase-score-fill" :style="{ width: score + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>
            <h3 class="progress-section-title">{{ t("skillBreakdown") }}</h3>
            <div class="progress-skills">
              <div v-for="skill in skillInsights" :key="skill.key" class="progress-skill-row">
                <div class="progress-skill-label">
                  <span>{{ skill.label }}</span>
                  <span>{{ skill.percent }}%</span>
                </div>
                <div class="progress-skill-track">
                  <div class="progress-skill-fill" :style="{ width: skill.percent + '%' }"></div>
                </div>
                <small class="progress-skill-tag">{{ skill.tag }}</small>
              </div>
            </div>
            <h3 class="progress-section-title">{{ t("lessonHistory") }}</h3>
            <div class="progress-lesson-grid">
              <div
                v-for="lesson in curriculumLessons"
                :key="lesson.lesson_id || lesson.week"
                class="progress-lesson-dot"
                :class="{
                  completed: lesson.completed,
                  active: lesson.index === activeLessonIndex && !lesson.completed,
                  locked: lesson.locked,
                }"
                :title="lesson.title"
              >
                <span v-if="lesson.completed">✓</span>
                <span v-else-if="lesson.locked">🔒</span>
                <span v-else>{{ lesson.lesson_number || lesson.week }}</span>
              </div>
            </div>
            <div v-if="reviewDueToday.length" style="margin-top:24px">
              <h3 class="progress-section-title">{{ t("reviewDueTodaySection") }}</h3>
              <ul class="review-due-list">
                <li v-for="item in reviewDueToday" :key="item.id">
                  <strong>{{ item.topic }}</strong> — from week {{ item.source_week }}
                </li>
              </ul>
            </div>
            <p v-else style="margin-top:16px;color:#64748b">{{ t("noDueReviews") }}</p>
          </div>

          <!-- Settings tab -->
          <div v-else-if="dashboardTab === 'settings'" class="dashboard-tab-panel">
            <h2 class="tab-panel-title">{{ t("settingsTitle") }}</h2>
            <div class="settings-section">
              <h3 class="settings-section-title">{{ t("settingsLanguages") }}</h3>
              <div class="settings-row">
                <div>
                  <strong>{{ t("settingsISpeak") }}</strong>
                  <small>{{ currentSpeakingLanguage }}</small>
                </div>
              </div>
              <div class="settings-row">
                <div>
                  <strong>{{ t("settingsImLearning") }}</strong>
                  <small>{{ currentLearningLanguage }}</small>
                </div>
              </div>
            </div>
            <div class="settings-section">
              <h3 class="settings-section-title">{{ t("settingsTts") }}</h3>
              <div class="settings-row">
                <div>
                  <strong>{{ t("settingsEnableTts") }}</strong>
                  <small>{{ t("readLessonWordsAloud") }}</small>
                </div>
                <label class="toggle-switch">
                  <input type="checkbox" v-model="settingsTtsEnabled" />
                  <span class="toggle-track"></span>
                </label>
              </div>
              <div class="settings-row">
                <div>
                  <strong>{{ t("settingsSpeakingSpeed") }}</strong>
                  <small>{{ settingsPlaybackRate }} wpm</small>
                </div>
                <input type="range" min="80" max="260" step="20" v-model.number="settingsPlaybackRate" class="settings-range" />
              </div>
              <div class="settings-row" v-if="voicesForLanguage.length">
                <div>
                  <strong>{{ t("settingsVoice") }}</strong>
                  <small>{{ voicesForLanguage.length }} available for {{ currentLearningLanguage }}</small>
                </div>
                <select v-model="selectedVoiceURI" class="voice-select">
                  <option v-for="v in voicesForLanguage" :key="v.voiceURI" :value="v.voiceURI">
                    {{ v.name }}
                  </option>
                </select>
              </div>
              <button class="secondary" style="margin-top:8px" @click="speakText('Hello! This is a voice test.', ttsLangCode)">
                {{ t("testVoice") }}
              </button>
            </div>
            <div class="settings-section">
              <h3 class="settings-section-title">Notifications</h3>
              <div class="settings-row">
                <div>
                  <strong>Practice reminders</strong>
                  <small>Get a reminder after 24 hours without practice</small>
                </div>
                <button
                  v-if="notificationsPermission !== 'granted'"
                  class="secondary"
                  @click="requestNotificationPermission"
                  :disabled="notificationsPermission === 'denied'"
                >
                  {{ notificationsPermission === 'denied' ? 'Blocked by browser' : 'Enable' }}
                </button>
                <span v-else class="settings-badge-on">✓ On</span>
              </div>
            </div>
            <div class="settings-section">
              <h3 class="settings-section-title">{{ t("settingsSession") }}</h3>
              <div class="settings-row">
                <div>
                  <strong>{{ t("startOver") }}</strong>
                  <small>{{ t("resetSessionDesc") }}</small>
                </div>
                <button class="secondary" @click="resetFlow">{{ t("reset") }}</button>
              </div>
            </div>
          </div>

          <div
            v-if="lessonPlayerOpen"
            class="lesson-player-overlay"
            role="dialog"
            aria-modal="true"
            aria-label="Lesson player"
          >
            <div class="lesson-player-modal lesson-studio">
              <aside class="lesson-studio-sidebar">
                <div class="lesson-studio-brand">Vlot</div>
                <div class="lesson-studio-profile">
                  <div class="learner-avatar">👩‍🎓</div>
                  <div>
                    <strong>{{ currentLearningLanguage }}</strong>
                    <p>{{ learnerLevelLabel }}</p>
                  </div>
                </div>
                <nav class="sidebar-nav">
                  <button class="nav-item" :class="{ active: lessonSidebarTab === 'curriculum' }" @click="lessonSidebarTab = 'curriculum'">
                    <span class="nav-icon">▤</span><span>{{ t("sidebarCurriculum") }}</span>
                  </button>
                  <button class="nav-item" :class="{ active: lessonSidebarTab === 'library' }" @click="lessonSidebarTab = 'library'">
                    <span class="nav-icon">▥</span><span>{{ t("sidebarLibrary") }}</span>
                  </button>
                  <button class="nav-item" :class="{ active: lessonSidebarTab === 'insights' }" @click="lessonSidebarTab = 'insights'">
                    <span class="nav-icon">◫</span><span>{{ t("sidebarInsights") }}</span>
                  </button>
                  <button class="nav-item" :class="{ active: lessonSidebarTab === 'settings' }" @click="lessonSidebarTab = 'settings'">
                    <span class="nav-icon">⚙</span><span>{{ t("sidebarSettings") }}</span>
                  </button>
                </nav>

                <!-- Curriculum tab -->
                <div v-if="lessonSidebarTab === 'curriculum'" class="sidebar-tab-content">
                  <p class="sidebar-tab-label">{{ t("yourLessons") }}</p>
                  <ul class="sidebar-lesson-list">
                    <li
                      v-for="lesson in curriculumLessons"
                      :key="lesson.lesson_id || lesson.week"
                      class="sidebar-lesson-item"
                      :class="{
                        'is-active': lesson.index === activeLessonIndex,
                        'is-completed': lesson.completed,
                        'is-locked': lesson.locked,
                      }"
                    >
                      <span class="sidebar-lesson-dot"></span>
                      <span class="sidebar-lesson-name">{{ lesson.title || `W${lesson.week} · L${lesson.lesson_number}` }}</span>
                      <span v-if="lesson.completed" class="sidebar-lesson-badge done">✓</span>
                      <span v-else-if="lesson.locked" class="sidebar-lesson-badge locked">🔒</span>
                    </li>
                  </ul>
                </div>

                <!-- Library tab -->
                <div v-else-if="lessonSidebarTab === 'library'" class="sidebar-tab-content">
                  <p class="sidebar-tab-label">{{ t("wordBank") }}</p>
                  <p v-if="!lessonLibraryVocab.length" class="sidebar-empty-note">
                    Words will appear here as you complete lessons.
                  </p>
                  <ul v-else class="sidebar-vocab-list">
                    <li v-for="item in lessonLibraryVocab" :key="item.term" class="sidebar-vocab-item">
                      <strong>{{ item.term }}</strong>
                      <small>{{ item.meaning }}</small>
                      <span v-if="item.example" class="sidebar-vocab-example">{{ item.example }}</span>
                    </li>
                  </ul>
                </div>

                <!-- Insights tab -->
                <div v-else-if="lessonSidebarTab === 'insights'" class="sidebar-tab-content">
                  <p class="sidebar-tab-label">{{ t("yourProgress") }}</p>
                  <div class="sidebar-stat-row">
                    <span>{{ t("lessonsDone") }}</span>
                    <strong>{{ completedLessonsCount }} / {{ curriculumLessons.length }}</strong>
                  </div>
                  <div class="sidebar-stat-row">
                    <span>{{ t("totalXp") }}</span>
                    <strong>{{ totalXpEarned }} XP</strong>
                  </div>
                  <div class="sidebar-stat-row">
                    <span>{{ t("level") }}</span>
                    <strong>{{ result?.assessment?.level || '—' }}</strong>
                  </div>
                  <p class="sidebar-tab-label" style="margin-top:14px">{{ t("skillScores") }}</p>
                  <div v-for="skill in skillInsights" :key="skill.key" class="sidebar-skill-row">
                    <div class="sidebar-skill-header">
                      <span>{{ skill.label }}</span>
                      <span>{{ skill.percent }}%</span>
                    </div>
                    <div class="sidebar-skill-bar">
                      <div class="sidebar-skill-fill" :style="{ width: skill.percent + '%' }"></div>
                    </div>
                  </div>
                </div>

                <!-- Settings tab -->
                <div v-else-if="lessonSidebarTab === 'settings'" class="sidebar-tab-content">
                  <p class="sidebar-tab-label">{{ t("lessonSettingsTitle") }}</p>
                  <div class="sidebar-setting-row">
                    <div>
                      <strong>{{ t("settingsTts") }}</strong>
                      <small>{{ t("readLessonAloud") }}</small>
                    </div>
                    <label class="toggle-switch">
                      <input type="checkbox" v-model="settingsTtsEnabled" />
                      <span class="toggle-track"></span>
                    </label>
                  </div>
                  <div class="sidebar-setting-row">
                    <div>
                      <strong>{{ t("settingsSpeakingSpeed") }}</strong>
                      <small>{{ settingsPlaybackRate }} wpm</small>
                    </div>
                    <input
                      type="range"
                      min="80"
                      max="260"
                      step="20"
                      v-model.number="settingsPlaybackRate"
                      class="sidebar-range"
                    />
                  </div>
                  <div v-if="voicesForLanguage.length" class="sidebar-setting-row">
                    <div>
                      <strong>{{ t("settingsVoice") }}</strong>
                      <small>{{ voicesForLanguage.length }} available</small>
                    </div>
                  </div>
                  <select
                    v-if="voicesForLanguage.length"
                    v-model="selectedVoiceURI"
                    class="voice-select sidebar-voice-select"
                  >
                    <option v-for="v in voicesForLanguage" :key="v.voiceURI" :value="v.voiceURI">
                      {{ v.name }}
                    </option>
                  </select>
                  <button
                    class="secondary"
                    style="margin-top:8px;width:100%"
                    @click="speakText('Hello! This is a voice test.', ttsLangCode)"
                  >{{ t("testVoice") }}</button>
                  <div class="sidebar-setting-row">
                    <div>
                      <strong>{{ t("learning") }}</strong>
                      <small>{{ currentLearningLanguage }}</small>
                    </div>
                  </div>
                </div>

                <button class="upgrade-btn" @click="closeLessonPlayer">← {{ t("backToDashboard") }}</button>
              </aside>

              <div class="lesson-studio-main">
                <div class="lesson-studio-top">
                  <div class="lesson-phase-progress">
                    <small>{{ t("currentProgress") }}</small>
                    <strong>Phase {{ activePhaseIndex + 1 }} of 5</strong>
                    <div class="assessment-progress">
                      <div class="assessment-progress-fill" :style="{ width: `${phaseProgressPercent}%` }"></div>
                    </div>
                  </div>
                  <button class="small-cta">{{ t("feedback") }}</button>
                </div>

                <header class="lesson-player-header">
                  <div>
                    <span class="phase-tag">{{ currentLessonPhase?.phase?.replaceAll("_", " ") }}</span>
                    <h3>{{ currentPhaseTitle }}</h3>
                    <p>{{ phaseSubtitleMap[currentLessonPhase?.phase] || currentLessonPhase?.goal }}</p>
                  </div>
                  <span>{{ activeLesson?.week ? `Week ${activeLesson.week}` : "" }}</span>
                </header>

                <section v-if="currentLessonPhase?.phase === 'warm_up'" class="lesson-stage-panel">
                  <article class="coach-message-card">
                    <div class="phase-goal-chip">{{ currentLessonPhase.goal }}</div>
                    <p style="margin-top:10px">{{ dynamicWarmupPrompt }}</p>

                    <!-- Starter word bank shown only in the very first lesson -->
                    <div v-if="isFirstLessonSession" class="starter-vocab-bank">
                      <h5>{{ t("starterWordsHint") }}</h5>
                      <div class="starter-vocab-grid">
                        <div v-for="item in starterVocabForLanguage" :key="item.term" class="starter-vocab-item">
                          <strong>{{ item.term }}</strong>
                          <span>{{ item.meaning }}</span>
                        </div>
                      </div>
                    </div>

                    <div class="lesson-input-block" style="margin-top:16px">
                      <label v-for="(question, idx) in warmupQuestions" :key="`wq-${idx}`">
                        <span>{{ question }}</span>
                        <input
                          v-model="lessonResponses.warm_up[idx]"
                          :placeholder="`Answer in ${currentLearningLanguage}`"
                        />
                      </label>
                    </div>
                  </article>
                </section>

                <section v-else-if="currentLessonPhase?.phase === 'input'" class="lesson-stage-panel">
                  <article class="input-vocab-card">
                    <h4>
                      {{ isFirstLessonSession ? 'Your first words in ' + currentLearningLanguage : 'New words &amp; phrases for this lesson' }}
                    </h4>
                    <p style="margin-bottom:12px;color:#475569">
                      Read each word, look at its meaning, and check the box when it makes sense to you.
                      Then use one of them in the sentence at the bottom.
                    </p>
                    <div class="vocab-grid">
                      <label
                        v-for="(item, idx) in inputVocabularyItems"
                        :key="`pack-${item.term}-${idx}`"
                        class="vocab-card"
                      >
                        <input type="checkbox" v-model="lessonResponses.input_vocab_checks[idx]" />
                        <div style="flex:1">
                          <strong>{{ item.term }}</strong>
                          <small>{{ item.meaning }}</small>
                          <small v-if="item.example_sentence" class="vocab-example">{{ item.example_sentence }}</small>
                        </div>
                        <button
                          class="tts-btn"
                          type="button"
                          @click.prevent="speakText(item.term, ttsLangCode)"
                          title="Listen"
                        >🔊</button>
                      </label>
                    </div>
                    <p class="vocab-progress">
                      {{ knownWordCount }} / {{ inputVocabularyItems.length }} understood
                    </p>
                    <div class="lesson-input-block" style="margin-top:14px">
                      <label>
                        <span>
                          Now pick one word from the list and write a short sentence with it in {{ currentLearningLanguage }}.
                          It doesn't have to be perfect — just try!
                        </span>
                        <textarea
                          v-model="lessonResponses.input_check"
                          :placeholder="`Example: ${inputVocabularyItems[0]?.term || 'Hello'} ...`"
                        />
                      </label>
                    </div>
                  </article>
                </section>

                <section v-else-if="currentLessonPhase?.phase === 'guided_practice'" class="lesson-stage-panel">
                  <p class="guided-hint" style="margin-bottom: 12px">
                    {{ t("needSupportLibrary") }}
                  </p>
                  <article class="exercise-card" v-for="(task, idx) in guidedExercisePrompts" :key="`gp-${idx}`">
                    <h4>Exercise {{ idx + 1 }}</h4>
                    <p v-if="task.prompt">{{ task.prompt }}</p>
                    <p v-if="!task.prompt && task.sentence_with_blank" class="guided-blank">{{ task.sentence_with_blank }}</p>
                    <p
                      v-else-if="
                        task.sentence_with_blank &&
                        task.sentence_with_blank.trim() &&
                        task.prompt &&
                        task.sentence_with_blank.trim() !== task.prompt.trim()
                      "
                      class="guided-blank"
                    >{{ task.sentence_with_blank }}</p>
                    <input
                      v-model="lessonResponses.guided_practice[idx]"
                      :placeholder="`Your answer in ${currentLearningLanguage}`"
                    />
                  </article>
                </section>

                <section v-else-if="currentLessonPhase?.phase === 'output_speaking'" class="lesson-stage-panel">
                  <article class="output-chat-card">
                    <h4>{{ t("speakingExercise") }}</h4>
                    <div class="phase-goal-chip" style="margin-bottom:10px">{{ currentLessonPhase.goal }}</div>
                    <p class="guided-hint" style="margin-bottom: 10px">
                      {{ t("speakingFirst") }}
                    </p>
                    <p>{{ outputScenario }}</p>
                    <div class="lesson-input-block" style="margin-top:14px">
                      <label>
                        <span>
                          Write or speak your response (aim for at least 2–3 sentences in {{ currentLearningLanguage }})
                        </span>
                        <textarea
                          v-model="lessonResponses.output_speaking"
                          rows="5"
                          :placeholder="`Write naturally in ${currentLearningLanguage}...`"
                        />
                      </label>
                      <button
                        type="button"
                        class="mic-btn"
                        :class="{ active: sttActive }"
                        @click="startStt(handleOutputSpeechResult)"
                        title="Click to speak — your speech will be transcribed"
                      >
                        {{ sttActive ? '🔴 Listening… (click to stop)' : '🎤 Speak your answer' }}
                      </button>
                      <div v-if="sttConfidence > 0" class="confidence-bar">
                        <span class="confidence-label">Pronunciation clarity: {{ sttConfidence }}%</span>
                        <div class="confidence-track">
                          <div
                            class="confidence-fill"
                            :style="{
                              width: sttConfidence + '%',
                              background: sttConfidence >= 70 ? '#0b7a6f' : sttConfidence >= 40 ? '#f59e0b' : '#ef4444',
                            }"
                          ></div>
                        </div>
                      </div>
                    </div>
                    <p v-if="outputPrimaryFeedback" class="assessment-tip" style="margin-top: 10px">
                      Coach feedback: {{ outputPrimaryFeedback }}
                    </p>
                    <div v-if="aiFeedback || aiFeedbackLoading" class="ai-feedback-block">
                      <span class="ai-feedback-label">🤖 AI Coach</span>
                      <p v-if="aiFeedbackLoading" class="ai-feedback-text">Analysing your answer…</p>
                      <p v-else class="ai-feedback-text">{{ aiFeedback }}</p>
                    </div>
                    <button
                      type="button"
                      class="send-btn"
                      style="margin-top: 10px; width: 100%; min-height: 46px"
                      @click="requestOutputFollowUpQuestion"
                    >
                      {{ t("generateFollowUp") }}
                    </button>

                    <div v-if="outputFollowUpQuestion" class="lesson-input-block" style="margin-top: 14px">
                      <label>
                        <span><strong>{{ outputFollowUpQuestion }}</strong></span>
                        <textarea
                          v-model="outputFollowUpAnswer"
                          rows="3"
                          :placeholder="`Answer the follow-up in ${currentLearningLanguage}...`"
                        />
                      </label>
                      <button
                        type="button"
                        class="mic-btn"
                        :class="{ active: sttActive }"
                        @click="startStt(handleOutputFollowUpSpeechResult)"
                        title="Click to speak your follow-up answer"
                      >
                        {{ sttActive ? '🔴 Listening… (click to stop)' : '🎤 Speak follow-up answer' }}
                      </button>
                      <p v-if="outputFollowUpFeedback" class="assessment-tip" style="margin-top: 10px">
                        {{ t("followUpFeedback") }}: {{ outputFollowUpFeedback }}
                      </p>
                    </div>
                    <p v-if="assessmentWeakAreas.length" class="weak-area-reminder">
                      {{ t("focusAreas") }} <strong>{{ assessmentWeakAreas.slice(0, 2).join(", ") }}</strong>
                    </p>
                  </article>
                </section>

                <section v-else class="lesson-stage-panel two-column">
                  <article class="feedback-summary-card">
                    <h4>{{ t("practicedToday") }}</h4>
                    <p>{{ currentLessonPhase.goal || "Great work completing this lesson!" }}</p>
                    <p v-if="assessmentStrongAreas.length" style="margin-top:8px">
                      Your strengths: <strong>{{ assessmentStrongAreas.join(", ") }}</strong>
                    </p>
                  </article>
                  <article class="feedback-stats-card">
                    <h4>{{ t("sessionStats") }}</h4>
                    <p>{{ t("xpEarnedInline") }}: <strong>+{{ xpEarned }}</strong></p>
                    <p>{{ t("accuracyInline") }}: <strong>{{ accuracyPercent }}%</strong></p>
                    <div v-if="feedbackCorrections.length" class="feedback-corrections">
                      <h5>{{ t("thingsToReview") }}</h5>
                      <ul>
                        <li v-for="item in feedbackCorrections" :key="item.before">
                          <strong>{{ t("insteadOf") }}</strong> {{ item.before }}<br />
                          <strong>{{ t("tryLabel") }}</strong> {{ item.correction }}<br />
                          <small>{{ item.note }}</small>
                          <p v-if="item.why" class="grammar-why">💡 {{ item.why }}</p>
                        </li>
                      </ul>
                    </div>
                    <div class="lesson-input-block" style="margin-top:14px">
                      <label>
                        <span>{{ t("nextLessonFocus") }}</span>
                        <textarea
                          v-model="lessonResponses.feedback_reflection"
                          rows="3"
                          placeholder="Write one short goal for next time..."
                        />
                      </label>
                    </div>
                  </article>
                </section>
              </div>
            </div>
            <div class="lesson-player-actions lesson-studio-footer">
              <p v-if="phaseValidationError" class="phase-validation-error">{{ phaseValidationError }}</p>
              <button class="secondary" :disabled="activePhaseIndex === 0 || lessonNetworkBusy" @click="previousLessonPhase">
                {{ t("previousPhase") }}
              </button>
              <button :disabled="lessonNetworkBusy" @click="nextLessonPhase">
                {{ activePhaseIndex === 4 ? t("finishLesson") : t("continueNextPhase") }}
              </button>
            </div>
          </div>

          <!-- Review session modal -->
          <div
            v-if="reviewSessionOpen && reviewDueToday.length"
            class="session-modal-overlay"
            role="dialog"
            aria-modal="true"
            aria-label="Review session"
          >
            <div class="session-modal">
              <div class="session-check" style="background:#0b7a6f">📚</div>
              <h2>Review Session</h2>
              <p style="color:#64748b;margin-bottom:16px">
                Topic {{ activeReviewIndex + 1 }} of {{ reviewDueToday.length }}
              </p>
              <div class="review-topic-card">
                <p class="review-topic-label">Recall this topic in {{ currentLearningLanguage }}:</p>
                <h3 class="review-topic-text">{{ reviewDueToday[activeReviewIndex]?.topic }}</h3>
                <p style="color:#64748b;font-size:13px">
                  Originally practiced in week {{ reviewDueToday[activeReviewIndex]?.source_week }}
                </p>
              </div>
              <div class="lesson-input-block" style="margin-top:14px">
                <textarea
                  :placeholder="`Write 1-2 sentences about this topic in ${currentLearningLanguage}…`"
                  rows="3"
                  style="width:100%;box-sizing:border-box"
                />
              </div>
              <div style="display:flex;gap:10px;margin-top:14px">
                <button
                  class="secondary"
                  style="flex:1"
                  @click="reviewSessionOpen = false"
                >Close</button>
                <button
                  style="flex:1"
                  :disabled="activeReviewIndex >= reviewDueToday.length - 1"
                  @click="activeReviewIndex = Math.min(activeReviewIndex + 1, reviewDueToday.length - 1)"
                >Next topic →</button>
              </div>
            </div>
          </div>

          <div
            v-if="sessionModalOpen"
            class="session-modal-overlay"
            role="dialog"
            aria-modal="true"
            aria-label="Session complete"
          >
            <div class="session-modal">
              <div class="session-check">✓</div>
              <h2>{{ t("sessionCompleteTitle") }}</h2>
              <p>
                {{ t("sessionCompleteBody") }}
              </p>

              <div class="session-progress-header">
                <span>{{ t("levelProgress") }}</span>
                <span>{{ levelProgressCurrent }} / {{ levelProgressTotal }} XP</span>
              </div>
              <div class="session-progress-track">
                <div class="session-progress-fill" :style="{ width: `${levelProgressPercent}%` }"></div>
              </div>

              <div class="session-stats">
                <article>
                  <small>{{ t("xpEarnedLabel") }}</small>
                  <strong>+{{ xpEarned }}</strong>
                </article>
                <article>
                  <small>{{ t("accuracyLabel") }}</small>
                  <strong>{{ accuracyPercent }}%</strong>
                </article>
              </div>

              <button class="session-primary" @click="closeSessionCompleteModal">{{ t("nextLesson") }}</button>
              <button class="session-secondary" @click="() => { closeSessionCompleteModal(); dashboardTab = 'progress'; }">{{ t("reviewMistakes") }}</button>
            </div>
          </div>
        </div>
    </section>

    <section v-if="error" class="card">
        <h3>{{ t("error") }}</h3>
      <div class="mono">{{ error }}</div>
    </section>
    </section>

    <footer v-if="!showDashboard" class="footer">
      <div class="footer-brand">Vlot</div>
      <div class="footer-links">
        <a href="#">{{ t("privacyPolicy") }}</a>
        <a href="#">{{ t("termsOfService") }}</a>
        <a href="#">{{ t("contactUs") }}</a>
      </div>
      <div class="footer-social">
        <a href="#">{{ t("twitter") }}</a>
        <a href="#">{{ t("linkedIn") }}</a>
      </div>
    </footer>
  </main>
</template>
