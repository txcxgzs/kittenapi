import { Router } from 'express'
import connectionRouter from './connection'
import variableRouter from './variable'
import listRouter from './list'
import onlineRouter from './online'
import userRouter from './user'
import adminRouter from './admin'
import authRouter from './auth'

const router = Router()

router.use('/connections', connectionRouter)
router.use('/connection', connectionRouter)
router.use('/var', variableRouter)
router.use('/list', listRouter)
router.use('/online', onlineRouter)
router.use('/user', userRouter)
router.use('/admin', adminRouter)
router.use('/auth', authRouter)

export default router
