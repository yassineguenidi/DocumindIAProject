import { PublicNavbar } from '../components/layout/PublicNavbar'
import { Footer } from '../components/layout/Footer'
import { Hero } from '../components/landing/Hero'
import { HowItWorks, Features, Security, Pricing, Faq, FinalCta } from '../components/landing/Sections'
import { usePageTitle } from '../hooks/usePageTitle'

export default function Home() {
    usePageTitle()

    return (
        <>
            <PublicNavbar />
            <main id="main">
                <Hero />
                <HowItWorks />
                <Features />
                <Security />
                <Pricing />
                <Faq />
                <FinalCta />
            </main>
            <Footer />
        </>
    )
}