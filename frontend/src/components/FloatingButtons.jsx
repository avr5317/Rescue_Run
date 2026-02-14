import { motion } from 'framer-motion';

export default function FloatingButtons({ onCreateRequest, crisisMode, onCrisisModeToggle }) {
  return (
    <div className="absolute bottom-6 right-6 z-[1001] flex flex-col items-end gap-3">
      {onCrisisModeToggle && (
        <motion.button
          type="button"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          onClick={onCrisisModeToggle}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium
            shadow-lg border backdrop-blur-xl
            ${crisisMode
              ? 'bg-amber-500/90 text-black border-amber-400'
              : 'bg-white/10 text-white border-white/20 hover:bg-white/20'
            }
          `}
        >
          <span>{crisisMode ? '🔴' : '⚪'}</span>
          Crisis Mode
        </motion.button>
      )}
      <motion.button
        type="button"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.05 }}
        onClick={onCreateRequest}
        className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold shadow-lg hover:shadow-xl transition-shadow"
      >
        <span className="text-xl">+</span>
        Request Help
      </motion.button>
    </div>
  );
}
