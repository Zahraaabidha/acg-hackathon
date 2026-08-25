import { useEffect } from "react";
import { useDashboardData } from "../hooks/useDashboardData";
import { LandingNav } from "../components/landing/LandingNav";
import { Hero } from "../components/landing/Hero";
import { StatsStrip } from "../components/landing/StatsStrip";
import { HowItWorks } from "../components/landing/HowItWorks";
import { ModelPreview } from "../components/landing/ModelPreview";
import { LandingFooter } from "../components/landing/LandingFooter";

export default function LandingPage() {
  const { data } = useDashboardData();

  useEffect(() => {
    document.body.classList.add("landing-page-active");

    return () => document.body.classList.remove("landing-page-active");
  }, []);

  return (
    <div className="landing-page relative" style={{ backgroundColor: "#0a0a0a" }}>
      <div className="absolute top-0 z-20 w-full">
        <LandingNav />
      </div>

      <Hero />

      <section className="bg-white py-14 sm:py-16">
        <div className="mx-auto max-w-[1200px] px-5 sm:px-8 lg:px-12">
          <StatsStrip data={data} />
        </div>
      </section>

      <HowItWorks />
      <ModelPreview data={data} />
      <LandingFooter />
    </div>
  );
}
