import Link from 'next/link';
// import { Dog } from 'lucide-react'; // Using emoji instead

export function Footer() {
  return (
    <footer style={{
      background: 'linear-gradient(135deg, #fed7aa 0%, #fce7f3 50%, #f3e8ff 100%)',
      borderTop: '4px solid #ec4899',
      paddingTop: '3rem',
      paddingBottom: '2rem'
    }}>
      <div style={{
        maxWidth: '80rem',
        margin: '0 auto',
        padding: '0 2rem'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '2rem'
        }}>
          {/* Logo and Description */}
          <div style={{
            gridColumn: 'span 2'
          }}>
            <Link href="/" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginBottom: '1rem',
              textDecoration: 'none'
            }}>
              <span style={{ fontSize: '2rem' }}>🐕</span>
              <span style={{
                fontSize: '1.5rem',
                fontWeight: 'bold',
                background: 'linear-gradient(45deg, #f59e0b, #ef4444, #ec4899, #8b5cf6)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                Dog Parking
              </span>
            </Link>
            <p style={{
              color: '#6b7280',
              marginBottom: '1rem',
              fontSize: '1rem',
              lineHeight: '1.6'
            }}>
              🌟 Premium dog care services that make tails wag! From daycare to grooming, 
              we've got everything your furry friend needs for a pawsome adventure! 🎾
            </p>
          </div>

          {/* Services */}
          <div>
            <h3 style={{
              fontSize: '1.125rem',
              fontWeight: 'bold',
              color: '#374151',
              marginBottom: '1rem'
            }}>
              🎯 Pawsome Services
            </h3>
            <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <li>
                <Link href="/venues?service=daycare" style={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  borderRadius: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#fef3c7';
                  e.currentTarget.style.color = '#92400e';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#6b7280';
                }}>
                  ☀️ Dog Daycare
                </Link>
              </li>
              <li>
                <Link href="/venues?service=boarding" style={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  borderRadius: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#fce7f3';
                  e.currentTarget.style.color = '#9d174d';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#6b7280';
                }}>
                  🏨 Dog Boarding
                </Link>
              </li>
              <li>
                <Link href="/venues?service=grooming" style={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  borderRadius: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#f3e8ff';
                  e.currentTarget.style.color = '#6b21a8';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#6b7280';
                }}>
                  ✂️ Dog Grooming
                </Link>
              </li>
              <li>
                <Link href="/venues?service=training" style={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  borderRadius: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#fed7aa';
                  e.currentTarget.style.color = '#9a3412';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#6b7280';
                }}>
                  🎓 Dog Training
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 style={{
              fontSize: '1.125rem',
              fontWeight: 'bold',
              color: '#374151',
              marginBottom: '1rem'
            }}>
              🏢 Company
            </h3>
            <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <li>
                <Link href="/about" style={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  borderRadius: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#fef3c7';
                  e.currentTarget.style.color = '#92400e';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#6b7280';
                }}>
                  ℹ️ About Us
                </Link>
              </li>
              <li>
                <Link href="/contact" style={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  borderRadius: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#fce7f3';
                  e.currentTarget.style.color = '#9d174d';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#6b7280';
                }}>
                  📞 Contact
                </Link>
              </li>
              <li>
                <Link href="/privacy" style={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  borderRadius: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#f3e8ff';
                  e.currentTarget.style.color = '#6b21a8';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#6b7280';
                }}>
                  🔒 Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" style={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  borderRadius: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#fed7aa';
                  e.currentTarget.style.color = '#9a3412';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#6b7280';
                }}>
                  📋 Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div style={{
          borderTop: '2px solid #ec4899',
          marginTop: '2rem',
          paddingTop: '2rem',
          textAlign: 'center'
        }}>
          <p style={{
            color: '#6b7280',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem'
          }}>
            © 2025 Dog Parking. All rights reserved. Made with 💖 for our furry friends! 🐾
          </p>
        </div>
      </div>
    </footer>
  );
}